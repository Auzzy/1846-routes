import csv

FIELDNAMES = ("name", "owner", "coord")

COMPANIES = {
    "Steamboat Company": lambda board, railroads, kwargs: _handle_steamboat_company(board, railroads, kwargs),
    "Meat Packing Company": lambda board, railroads, kwargs: _handle_meat_packing_company(board, railroads, kwargs),
    "Mail Contract": lambda board, railroads, kwargs: _handle_mail_contract(board, railroads, kwargs)
}

STEAMBOAT_COORDS = ["B8", "C5", "D14", "G19", "I1"]
MEAT_PACKING_COORDS = ["D6", "I1"]

def _handle_steamboat_company(board, railroads, kwargs):
    owner = kwargs.get("owner")
    coord = kwargs["coord"]
    if not owner or not coord:
        return

    if owner not in railroads:
        raise ValueError("Assigned the Steamboat Company to an unrecognized or unfounded railroad: {}".format(owner))

    if coord not in STEAMBOAT_COORDS:
        raise ValueError("Placed the Steamboart Company token on an invalid space: {}".format(coord))

    board.place_seaport_token(coord, railroads[owner])

def _handle_meat_packing_company(board, railroads, kwargs):
    owner = kwargs.get("owner")
    coord = kwargs["coord"]
    if not owner or not coord:
        return

    if owner not in railroads:
        raise ValueError("Assigned the Meat Packing Company to an unrecognized or unfounded railroad: {}".format(owner))

    if coord not in MEAT_PACKING_COORDS:
        raise ValueError("Placed the Meat Packing Company token on an invalid space: {}".format(coord))

    board.place_meat_packing_token(coord, railroads[owner])

def _handle_mail_contract(board, railroads, kwargs):
    owner = kwargs.get("owner")
    if not owner:
        return

    if owner not in railroads:
        raise ValueError("Assigned the Mail Contract to an unrecognized or unfounded railroad: {}".format(owner))

    railroads[owner].assign_mail_contract()

def load_from_csv(board, railroads, companies_filepath):
    if companies_filepath:
        with open(companies_filepath, newline='') as companies_file:
            return load(board, railroads, tuple(csv.DictReader(companies_file, fieldnames=FIELDNAMES, delimiter=';', skipinitialspace=True)))

def load(board, railroads, companies_rows):
    if not companies_rows:
        return

    private_company_names = [company["name"] for company in companies_rows]
    if len(private_company_names) != len(set(private_company_names)):
        raise ValueError("Each private company should only have a single entry.")

    for company_kwargs in companies_rows:
        name = company_kwargs.get("name")
        if name not in COMPANIES:
            raise ValueError("An unrecognized private company was provided: {}".format(name))

        COMPANIES[name](board, railroads, company_kwargs)