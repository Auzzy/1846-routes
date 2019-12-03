import itertools
import logging
import math
import multiprocessing
import os
import queue

LOG = logging.getLogger(__name__)


class RailroadRoutes:
    @staticmethod
    def run(railroad, routes, board, phase):
        run_routes_by_train = {}
        for train in self.routes:
            run_routes_by_train[train] = [route.run(self.board, train, self.railroad, phase) for route in routes[train]]

        return RailroadRoutes(railroad, run_routes_by_train)

    def __init__(self, railroad, routes):
        self.railroad = railroad
        self.routes = routes

    def calculate_best_route_set(self, phase):
        route_sets = self._get_route_sets()

        if self.railroad.has_mail_contract:
            for route_set in route_sets:
                route = max(route_set, key=lambda run_route: len(run_route.cities))
                route.add_mail_contract()

        LOG.debug("Found %d route sets.", len(route_sets))
        for route_set in route_sets:
            for run_route in route_set:
                LOG.debug("{}: {} ({})".format(run_route.train, str(run_route), run_route.value))
            LOG.debug("")

        return max(route_sets, key=lambda route_set: sum(route.value for route in route_set)) if route_sets else {}

    def _get_route_sets(self):
        manager = multiprocessing.Manager()
        input_queue = manager.Queue()

        sorted_routes_by_train = {train: sorted(routes, key=lambda route: route.value, reverse=True) for train, routes in self.routes.items()}

        proc_count = os.cpu_count()
        best_route_sets = []
        with multiprocessing.Pool(processes=proc_count) as pool:
            # Using half the processes as workers seems to result in faster processing times.
            worker_count = proc_count / 2
            for train_set in self._get_train_sets():
                sorted_routes = [sorted_routes_by_train[train] for train in train_set]

                if all(sorted_routes):
                    # Cut routes into 1 chunk per worker and put it on the queue
                    chunk_size = math.ceil(len(sorted_routes[0]) / worker_count)
                    for root_routes in chunk_sequence(sorted_routes[0], chunk_size):
                        input_queue.put_nowait([root_routes] + sorted_routes[1:])

                    # Allow the workers to compare notes on what the best route value is
                    global_best_value = manager.Value('i', 0)

                    # Give each worker the input queue and the best value reference
                    worker_promises = []
                    for k in range(math.ceil(worker_count)):
                        promise = pool.apply_async(_find_best_sub_route_set_worker, (input_queue, global_best_value))
                        worker_promises.append(promise)

                    # Add the results to the list
                    for promise in worker_promises:
                        values = promise.get()
                        best_route_sets.extend(values)

        return best_route_sets

    def chunk_sequence(sequence, chunk_length):
        """Yield successive n-sized chunks from l."""
        for index in range(0, len(sequence), chunk_length):
            yield sequence[index:index + chunk_length]

    def _get_train_sets(self):
        train_sets = []
        for train_count in range(1, len(self.railroad.trains) + 1):
            train_combinations = set(itertools.combinations(self.railroad.trains, train_count))
            train_sets += [tuple(sorted(train_set, key=lambda train: train.collect)) for train_set in train_combinations]
        return train_sets

    def _find_best_sub_route_set_worker(input_queue, global_best_value):
        best_route_sets = []
        while True:
            try:
                sorted_routes = input_queue.get_nowait()
                best_route_set = _find_best_sub_route_set(global_best_value, sorted_routes)
    
                if best_route_set:
                    best_route_sets.append(best_route_set)
            except queue.Empty:
                return best_route_sets

    def _find_best_sub_route_set(global_best_value, sorted_routes, selected_routes=None):
        selected_routes = selected_routes or []

        minor_routes = []
        best_route_set = selected_routes
        best_route_set_value = route_set_value(selected_routes)
        if best_route_set_value > global_best_value.value:
            global_best_value.value = best_route_set_value

        for minor_route in sorted_routes[0]:
            if not _is_overlapping(minor_route, selected_routes):
                if sorted_routes[1:]:
                    # Already selected routes + the current route + the maximum possible value of the remaining train routes.
                    max_possible_route_set = selected_routes + [minor_route] + [routes[0] for routes in sorted_routes[1:]]
                    max_possible_value = route_set_value(max_possible_route_set)
                    # That must be more than the current best route set value, or we bail from this iteration.
                    if max_possible_value <= global_best_value.value:
                        return best_route_set

                    sub_route_set = _find_best_sub_route_set(global_best_value, sorted_routes[1:], selected_routes + [minor_route])
                    sub_route_set_value = route_set_value(sub_route_set)
                    if sub_route_set_value >= global_best_value.value:
                        best_route_set = sub_route_set
                        best_route_set_value = sub_route_set_value
                        global_best_value.value = sub_route_set_value
                else:
                    return selected_routes + [minor_route]
        return best_route_set

    def _is_overlapping(active_route, routes_to_check):
        return any(True for route in routes_to_check if active_route.overlap(route)) if routes_to_check else False

    def route_set_value(route_set):
        return sum(route.value for route in route_set)