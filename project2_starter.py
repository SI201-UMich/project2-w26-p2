# SI 201 HW4 (Library Checkout System)
# Your name: Lena Dao
# Your student id: 07148470
# Your email: lkdao@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# e.g.: Asked ChatGPT for hints on debugging and for suggestions on overall code structure
# - I used Gemini to help me understand new material I was not familiar with, such as working with file paths, joining directories, and reading error messages. 
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
# - Yes - I believe I used it ethically, solely for hints about what was wrong with parts of my code and to clarify concepts. Still, I wrote, tested, and understood my own work.
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    
    results = []

    if not os.path.exists(html_path):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        html_path = os.path.join(base_dir, html_path)

    with open(html_path, "r", encoding="utf-8-sig") as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")

    title_tags = soup.find_all("div", attrs={"data-testid": "listing-card-title"})

    for tag in title_tags:
        # get the listing title text from the div
        listing_title = tag.get_text(strip=True)
        # get the id attribute, like "title_1944564"
        title_id = tag.get("id", "")
        
        # find the number inside the id string
        numbers = re.findall(r"\d+", title_id)
        
        # if a number was found, save the title and listing id as a tuple
        if numbers:
            listing_id = numbers[0]
            results.append((listing_title, listing_id))

    return results


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """

    base_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "html_files", f"listing_{listing_id}.html")

    with open(file_path, "r", encoding="utf-8-sig") as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    # default values in case something is missing
    policy_number = ""
    host_type = "regular"
    host_name = ""
    room_type = "Entire Room"
    location_rating = 0.0

    # find the policy number text
    policy_match = re.search(r"Policy number:\s*(.*?)\s+(Languages|Language|Response rate|Response time)", page_text)

    if policy_match:
        raw_policy = policy_match.group(1).strip()

        if raw_policy.lower() == "pending":
            policy_number = "Pending"
        elif raw_policy.lower() == "exempt":
            policy_number = "Exempt"
        else:
            policy_number = raw_policy

    # check if the host is a Superhost
    if "Superhost" in page_text:
        host_type = "Superhost"

    # find the host name
    host_match = re.search(r"Hosted by (.*?) Joined in", page_text)

    if host_match:
        host_name = host_match.group(1).strip()

    # find the room type from the listing subtitle
    room_match = re.search(r"(Entire|Private|Shared).*?hosted by", page_text)

    if room_match:
        room_text = room_match.group(0)

        if "Private" in room_text:
            room_type = "Private Room"
        elif "Shared" in room_text:
            room_type = "Shared Room"
        else:
            room_type = "Entire Room"

    # find the location rating
    location_match = re.search(r"Location\s+([0-9]\.[0-9])", page_text)

    if location_match:
        location_rating = float(location_match.group(1))

    return {
        listing_id: {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating
        }
    }


def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    
    listing_data = []
    listing_results = load_listing_results(html_path)

    for listing in listing_results:
        # get the title and id from each tuple
        listing_title = listing[0]
        listing_id = listing[1]

        # get the rest of the information for this listing
        details = get_listing_details(listing_id)

        # pull each value from the nested dictionary
        policy_number = details[listing_id]["policy_number"]
        host_type = details[listing_id]["host_type"]
        host_name = details[listing_id]["host_name"]
        room_type = details[listing_id]["room_type"]
        location_rating = details[listing_id]["location_rating"]

        # put all listing information into one tuple
        listing_tuple = (
            listing_title,
            listing_id,
            policy_number,
            host_type,
            host_name,
            room_type,
            location_rating
        )

        # add the tuple to the final list
        listing_data.append(listing_tuple)

    return listing_data


def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.

    Sort by Location Rating (descending).

    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to

    Returns:
        None
    """

    sorted_data = sorted(data, key=lambda listing: listing[6], reverse=True)

    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Listing Title",
            "Listing ID",
            "Policy Number",
            "Host Type",
            "Host Name",
            "Room Type",
            "Location Rating"
        ])

        for listing in sorted_data:
            writer.writerow(listing)


def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.

    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).

    Args:
        data (list[tuple]): The list returned by create_listing_database()

    Returns:
        dict: {room_type: average_location_rating}
    """
    
    ratings_by_room_type = {}

    for listing in data:
        room_type = listing[5]
        location_rating = listing[6]

        # skip listings with no location rating
        if location_rating == 0.0:
            continue

        # create a new list for this room type if needed
        if room_type not in ratings_by_room_type:
            ratings_by_room_type[room_type] = []

        # add the rating to the correct room type
        ratings_by_room_type[room_type].append(location_rating)

    averages = {}

    for room_type in ratings_by_room_type:
        ratings = ratings_by_room_type[room_type]
        average = sum(ratings) / len(ratings)
        averages[room_type] = average

    return averages


def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.

    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()

    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    
    invalid_listings = []

    for listing in data:
        listing_id = listing[1]
        policy_number = listing[2]

        # skip pending and exempt listings
        if policy_number == "Pending" or policy_number == "Exempt":
            continue

        # check if the policy number matches one of the two valid formats
        valid_format_1 = re.fullmatch(r"20\d\d-00\d\d\d\dSTR", policy_number)
        valid_format_2 = re.fullmatch(r"STR-000\d\d\d\d", policy_number)

        if not valid_format_1 and not valid_format_2:
            invalid_listings.append(listing_id)

    return invalid_listings


def google_scholar_searcher(query):
    """
    EXTRA CREDIT

    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    
    # Google Scholar search page
    url = "https://scholar.google.com/scholar"

    # send the search query
    params = {"q": query}

    # send a request to Google Scholar using the search query
    # ex: if query = "airbnb", the request goes to https://scholar.google.com/scholar?q=airbnb
    response = requests.get(url, params=params)
    # get the HTML from the page
    soup = BeautifulSoup(response.text, "html.parser")

    # store all article titles in a list
    titles = []

    # find each title section on the page
    for title_section in soup.find_all("h3", class_="gs_rt"):
        # find the link tag inside the title section
        link = title_section.find("a")

        # if there is a link, get the title text and save it
        if link:
            title = link.get_text(strip=True)
            titles.append(title)

    return titles


class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")

        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)


    def test_load_listing_results(self):
        # Check that the number of listings extracted is 18.
        self.assertEqual(len(self.listings), 18)

        # Check that the FIRST (title, id) tuple is ("Loft in Mission District", "1944564").
        self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))


    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]

        # Call get_listing_details() on each listing id above and save results in a list.
        details_list = []
        for listing_id in html_list:
            details_list.append(get_listing_details(listing_id))

        # Spot-check a few known values by opening the corresponding listing_<id>.html files.
        # 1) Check that listing 467507 has the correct policy number "STR-0005349".
        # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
        # 3) Check that listing 1944564 has the correct location rating 4.9.

        self.assertEqual(details_list[0]["467507"]["policy_number"], "STR-0005349")
        self.assertEqual(details_list[2]["1944564"]["host_type"], "Superhost")
        self.assertEqual(details_list[2]["1944564"]["room_type"], "Entire Room")
        self.assertEqual(details_list[2]["1944564"]["location_rating"], 4.9)
        

    def test_create_listing_database(self):
        # Check that each tuple in detailed_data has exactly 7 elements:
        # (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
        for listing in self.detailed_data:
            self.assertEqual(len(listing), 7)

        # Spot-check the LAST tuple is ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8).
        self.assertEqual(self.detailed_data[-1], ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8))


    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        # Call output_csv() to write the detailed_data to a CSV file.
        output_csv(self.detailed_data, out_path)

        # Read the CSV back in and store rows in a list.
        rows = []
        with open(out_path, "r", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            for row in reader:
                rows.append(row)

        # Check that the first data row matches ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"].
        self.assertEqual(rows[1], ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"])

        os.remove(out_path)


    def test_avg_location_rating_by_room_type(self):
        # Call avg_location_rating_by_room_type() and save the output.
        averages = avg_location_rating_by_room_type(self.detailed_data)

        # Check that the average for "Private Room" is 4.9.
        self.assertEqual(averages["Private Room"], 4.9)


    def test_validate_policy_numbers(self):
        # Call validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.
        invalid_listings = validate_policy_numbers(self.detailed_data)

        # Check that the list contains exactly "16204265" for this dataset.
        self.assertEqual(invalid_listings, ["16204265"])


def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)