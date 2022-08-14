import argparse
from csv import DictReader
import json
from datetime import datetime, timedelta


parser = argparse.ArgumentParser()
parser.add_argument("data", help="Input datafile path", type=str)
parser.add_argument("origin", help="Origin airport", type=str)
parser.add_argument("destination", help="Destination airport", type=str)
parser.add_argument("--bags", help="Number of bags", type=int, default=0)
args = parser.parse_args()


# read available flights
flights = []
with open(args.data) as fh:
    reader = DictReader(fh)
    for flight in reader:
        flights.append(flight)

# ensure flights are sorted (they are in CSV, but who knows)
flights = sorted(flights, key=lambda flight: flight["departure"])


def find_flights(origin: str, destination: str, requested_bags: int = 0):
    """
    Return valid combinations of flights for given origin, destination, and min number of bags
    """
    next_flights = []
    for i, flight in enumerate(flights):
        if flight["origin"] == origin and int(flight["bags_allowed"]) >= requested_bags:
            next_flights += get_next_flights([flight], destination, requested_bags, flights[i+1:])
    return next_flights


def get_next_flights(previous_flights: list, destination: str, requested_bags: int, flights_to_consider: list):
    """
    Return all valid combinations of flights given the previous list of flights, the final destination and a min number of bags, taking into account a given list of available flights to consider.
    """
    last_flight = previous_flights[-1]
    last_airport = last_flight["destination"]

    # termination conditions
    if last_airport == destination:  # already arrived to destination
        return [previous_flights]
    
    if len(flights_to_consider) == 0:  # no more options to try
        return []

    previous_airports = {flight["destination"] for flight in previous_flights} | {flight["origin"] for flight in previous_flights}

    next_flights = []
    for i, flight in enumerate(flights_to_consider):
        # list of conditions for flight being considered to be a valid option
        connecting_flight = flight["origin"] == last_flight["destination"]
        reasonable_layover = timedelta(hours=1) <= datetime.fromisoformat(flight["departure"]) - datetime.fromisoformat(last_flight["arrival"]) <= timedelta(hours=6)
        not_repeated_airports = flight["destination"] != previous_airports
        enough_bags = int(flight["bags_allowed"]) >= requested_bags

        if connecting_flight and reasonable_layover and not_repeated_airports and enough_bags:
            selected_flights = previous_flights[:]
            selected_flights.append(flight)
            # We only need to consider from i+1 because all previous flights depart earlier
            next_flights += get_next_flights(selected_flights, destination, requested_bags, flights_to_consider[i+1:])

    return next_flights
            
    
def generate_trip(combination, bags_count):
    """
    Create JSON-like structure for the trip, given the combination of flights and the requested n of bags.
    """
    travel_time = datetime.fromisoformat(combination[-1]["arrival"]) - datetime.fromisoformat(combination[-1]["departure"])
    return {
        "flights": combination,
        "origin": combination[0]["departure"],
        "destination": combination[-1]["destination"],
        "bags_allowed": min(flight["bags_allowed"] for flight in combination),
        "bags_count": bags_count,
        "total_price": sum(float(flight["base_price"]) for flight in combination),
        "travel_time": str(travel_time)
    }


origin = args.origin
destination = args.destination
bags_count = args.bags

combinations = find_flights(origin, destination, bags_count)

trips = sorted([generate_trip(combination, bags_count) for combination in combinations], key=lambda trip: trip["total_price"])

print(json.dumps(trips, indent=4))