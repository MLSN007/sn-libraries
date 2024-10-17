import json
import os


def create_fb_config(user_name, app_name, page_name):
    """
    Creates a JSON configuration file for a Facebook app based on the provided user name, app name, and page name.

    This function generates a configuration dictionary with placeholders for Facebook app credentials and page information.
    It then writes this configuration to a JSON file in the 'config_files' directory. The file name is dynamically generated
    based on the input parameters.

    :param user_name: The name of the user (e.g., 'JK')
    :param app_name: The name of the Facebook app (e.g., 'JK Travel')
    :param page_name: The name of the Facebook page associated with the app (e.g., 'JK Travel')
    :output_file: The path to the JSON configuration file, which is dynamically generated based on the input parameters.
    """
    config = {
        "user_id": f"FB_{user_name}_User_id",
        "app_id": f"FB_{app_name}_App_id",
        "app_secret": f"FB_{app_name}_App_secret",
        "access_token": f"FB_{app_name}_{page_name}_App_token",
        "page_id": f"FB_{page_name}_Pg_id",
        "user_token": f"FB_{app_name}_user_token",
    }

    output_file = os.path.join(
        "config_files", f"FB_{user_name}_{app_name}_{page_name}_config.json"
    )

    # Write the configuration to a JSON file
    with open(output_file, "w", encoding="utf-8") as f:  # Specify encoding
        json.dump(config, f, indent=4)

    print(f"Configuration file created: {output_file}")


if __name__ == "__main__":
    create_fb_config(user_name="LS", app_name="M001", page_name="ES")
