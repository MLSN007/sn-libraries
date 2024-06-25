# %%
from hikerapi import Client
hiker_api_key = os.environ["HikerAPI_key"]
cl = Client(token=hiker_api_key)  

# %%
print(type(cl))

# %%
print(hiker_api_key)

# %% [markdown]
# ### Hiker API - Get user info

# %%


user_info = cl.user_by_username_v2("huelvafoodie")

pprint(user_info)

# %% [markdown]
# ## Extract the most important Huelva influencers profiles by name
# ### store them in a JSON file

# %%
import os
import json
from hikerapi import Client

def fetch_and_save_profiles(usernames, output_file="instagram_profiles.json"):
    """Fetches user profiles from HikerAPI and saves the data to a JSON file.

    Args:
        usernames: A list of Instagram usernames to fetch.
        output_file: The path to the JSON file where data will be saved.
    """
    
    # Load your HikerAPI key securely from an environment variable
    hiker_api_key = os.environ.get("HikerAPI_key")
    if not hiker_api_key:
        raise ValueError("HikerAPI_key environment variable not found.")

    # Create the HikerAPI client
    cl = Client(token=hiker_api_key)

    all_profile_data = []

    for username in usernames:
        try:
            user_info = cl.user_by_username_v2(username)

            # If the request is successful, add it to the list
            if user_info['status'] == 'ok':
                all_profile_data.append(user_info)
            else:
                print(f"Error fetching data for {username}: {user_info.get('error')}")
        except Exception as e:
            print(f"Error fetching data for {username}: {e}")

    # Save the data to a JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_profile_data, f, ensure_ascii=False, indent=4)




# %%
# call the function to fetch the information
usernames_to_fetch = ["capturolavida_emn",
                      "huelvafoodie",
                      "laesenciadehuelva",
                      "huelvagram",
                      "agendahuelva",
                      "huelva_secreta",
                      "huelva.explore",
                      "huelva24com",
                      "huelvainformacion",
                      "huelvahoy",
                      "huelvaoriginal"]

# Call the function to fetch and save profiles
fetch_and_save_profiles(usernames_to_fetch)    # add arg for output_file - default "instagram_profiles.json"

# %% [markdown]
# ## Extract relevant information from the JSON and store it in a pandas data frame
# ## and, latter, store in a .csv file
# ## to access it with Excel or Google Sheets

# %%
import os
import json
import pandas as pd

def extract_profile_data_from_json(input_file="instagram_profiles.json", output_file="instagram_profiles.csv"):
    """Loads Instagram profile data from a JSON file, extracts relevant fields,
    creates a Pandas DataFrame, and exports it to a CSV file.

    Args:
        input_file: The path to the JSON file containing the profile data.
        output_file: The path to save the CSV file.
    """

    with open(input_file, "r", encoding="utf-8") as f:
        all_profile_data = json.load(f)

    extracted_data = []

    for profile in all_profile_data:
        if profile["status"] == "ok":
            user = profile["user"]
            extracted_data.append({
                "username": user["username"],
                "full_name": user["full_name"],
                "instagram_id": user.get("pk", user.get("pk_id")),  # Extract the ID (either "pk" or "pk_id")
                "category": user["category"],
                "biography": user["biography"],
                "followers": user["follower_count"],
                "following": user["following_count"],
                "is_private": user["is_private"],
                "is_business": user["is_business"],
                "is_verified": user["is_verified"],
                "media_count": user["media_count"],
                "fb_page_id": str(user["page_id"]),
                "fb_page_name": user["page_name"],
                "profile_pic_url": user["profile_pic_url"],
                "external_url": user.get("external_url"), # Use get() to handle missing keys
                "bio_links": [link["url"] for link in user.get("bio_links", [])] # Extract URLs from bio links
            })

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(extracted_data)

    # Export the DataFrame to a CSV file (for Google Sheets)
    df.to_csv(output_file, index=False)

# Example Usage: 
extract_profile_data_from_json()    # Using default file names
                                    # input_file="instagram_profiles.json",
                                    # output_file="instagram_profiles.csv"





