# To handle operations related to the Flight table.
import mysql.connector
from datetime import datetime, timedelta
from collections import deque
from config.database_config import get_db_connection  

class FlightRepository:
    def __init__(self):
        self.connection = get_db_connection()
        self.cursor = self.connection.cursor()

    # Define the function to add flight
    def add_flight(self, flight):
    # Retrieve flight details from the flight object using getter methods
        airline_code = flight.get_airline_code()
        distance_km = flight.get_distance_km()
        dep_time = flight.get_dep_time()
        arri_time = flight.get_arri_time()
        dep_port = flight.get_dep_port()
        arri_port = flight.get_arri_port()

        # SQL query to insert a new flight record into the Flight table
        query = """
            INSERT INTO Flight (airline_code, distance_km, dep_time, arri_time, dep_port, arri_port)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # Execute the SQL query with the flight details
        self.cursor.execute(query, (airline_code, distance_km, dep_time, arri_time, dep_port, arri_port))
        # Commit the transaction to save changes to the database
        self.connection.commit()

        # Get the auto-incremented flight number (last inserted ID)
        inserted_flight_no = self.cursor.lastrowid
        # Display the inserted flight number
        print(f"Flight added successfully. Flight Number: {inserted_flight_no}")
        return inserted_flight_no

    # Define the function to delete flight
    def delete_flight(self, flight_no):
        # SQL query to delete a flight record based on the flight number
        query = "DELETE FROM Flight WHERE flight_no = %s"
        # Execute the SQL query with the provided flight number
        self.cursor.execute(query, (flight_no,))
       # Commit the transaction to apply the changes to the database
        self.connection.commit()

        # Check how many rows were affected. Return True if 1 or more rows were affected else False
        if self.cursor.rowcount > 0:
            return True 
        else:
            return False

    # Find a direct flight
    def _find_direct_flights(self, date, departure_airport, destination_airport):
        """Find direct flights only."""
        query = """
            SELECT * FROM Flight 
            WHERE dep_port = %s AND arri_port = %s AND DATE(dep_time) = %s
        """
        self.cursor.execute(query, (departure_airport, destination_airport, date))


    # Find the itineraries
    def _find_itineraries(self, date, departure_airport, destination_airport, max_stops):
        """Find possible connecting flights with a maximum of 2 stops using BFS."""
        itinerary_list = []

        # Use BFS to find paths between departure_airport and destination_airport
        queue = deque([(departure_airport, [], None, 0)])  # (current_airport, flights_taken, last_arrival_time, stops_count)
        visited = set()

        while queue:
            current_airport, flights_taken, last_arrival_time, stops_count = queue.popleft()

            if current_airport in visited:
                continue
            visited.add(current_airport)

            if stops_count > max_stops:
                continue  # Skip this branch if stops exceed max_stops

            # Find all flights from the current airport
            query = """
                SELECT * FROM Flight 
                WHERE dep_port = %s AND DATE(dep_time) = %s
            """
            self.cursor.execute(query, (current_airport, date))
            connecting_flights = self.cursor.fetchall()

            for flight in connecting_flights:
                flight_no, airline_code, distance_km, dep_time, arri_time, dep_port, arri_port, seats = flight

                # Skip direct flights (i.e., where arrival port matches the destination airport)
                if dep_port == departure_airport and arri_port == destination_airport:
                    continue  # Skip direct flights                

                # Ensure layover time between flights (e.g., at least 1 hour)
                if last_arrival_time is None or (dep_time > last_arrival_time + timedelta(hours=1)):
                    new_flights_taken = flights_taken + [flight]

                    # If the destination is reached, add the itinerary to the list
                    if arri_port == destination_airport:
                        itinerary_list.append(new_flights_taken)
                    else:
                        # Continue BFS from the new airport, increasing the stops count
                        queue.append((arri_port, new_flights_taken, arri_time, stops_count + 1))

        return itinerary_list


    # Define the function to find flights
    def find_flights(self, date, departure_airport, destination_airport):
        """Find direct flights and possible connecting itineraries (max 2 stops)."""
        direct_flights = self._find_direct_flights(date, departure_airport, destination_airport)

        # Find possible connecting itineraries with a maximum of 2 stops
        itineraries = self._find_itineraries(date, departure_airport, destination_airport, max_stops=2)

        return direct_flights + itineraries