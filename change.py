import requests
from github import Github
import sys
import json
from datetime import datetime

class LootLabsGenerator:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://creators.lootlabs.gg/api/public/content_locker"
        self.encryptor_url = "https://creators.lootlabs.gg/api/public/url_encryptor"
        
    def encrypt_url(self, destination_url, use_get=False):
        """Encrypt a URL for use with the &data parameter (anti-bypass)"""
        if use_get:
            # GET request method
            params = {
                'destination_url': destination_url,
                'api_token': self.api_token
            }
            try:
                response = requests.get(self.encryptor_url, params=params)
                response.raise_for_status()
                result = response.json()
                
                if result.get("type") == "fetched":
                    return result.get("message")
                else:
                    print(f"Encryption failed: {result.get('message', 'Unknown error')}")
                    return None
            except requests.RequestException as e:
                print(f"Encryption request failed: {e}")
                return None
        else:
            # POST request method
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "destination_url": destination_url
            }
            
            try:
                response = requests.post(self.encryptor_url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                
                if result.get("type") == "created":
                    return result.get("message")
                else:
                    print(f"Encryption failed: {result.get('message', 'Unknown error')}")
                    return None
                    
            except requests.RequestException as e:
                print(f"Encryption request failed: {e}")
                return None
    
    def get_github_content(self, raw_url):
        """Fetch content from GitHub raw URL"""
        try:
            response = requests.get(raw_url)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            print(f"Error fetching GitHub content: {e}")
            return None
    
    def create_anti_bypass_link(self, base_loot_url, new_destination_url):
        """Create an anti-bypass link by encrypting a new destination URL"""
        encrypted_data = self.encrypt_url(new_destination_url)
        
        if encrypted_data:
            # Extract the short code from the base URL
            # e.g., https://loot-link.com/s?XiBpFlWo -> XiBpFlWo
            if "loot-link.com/s?" in base_loot_url or "lootdest.org/s?" in base_loot_url:
                short_code = base_loot_url.split("?")[-1]
                domain = "loot-link.com" if "loot-link.com" in base_loot_url else "lootdest.org"
                anti_bypass_url = f"https://{domain}/s?{short_code}&data={encrypted_data}"
                return anti_bypass_url
            else:
                print("Invalid LootLabs URL format")
                return None
        else:
            print("Failed to encrypt destination URL")
            return None
    
    def generate_lootlabs_link(self, title, final_url, tier_id=1, tasks=3, theme=3):
        """Generate LootLabs link via API"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "title": title,
            "url": final_url,
            "tier_id": tier_id,
            "number_of_tasks": tasks,
            "theme": theme
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Debug: Print the full response to understand its structure
            print(f"🔍 API Response: {json.dumps(result, indent=2)}")
            
            # Handle different response formats
            if isinstance(result, dict):
                if result.get("type") in ["created", "fetch"]:
                    # Handle case where message is a list
                    message = result.get("message")
                    if isinstance(message, list) and len(message) > 0:
                        return message[0]["loot_url"]
                    elif isinstance(message, dict):
                        return message["loot_url"]
                    else:
                        print(f"Unexpected message format: {message}")
                        return None
                else:
                    print(f"Error: {result.get('message', 'Unknown error')}")
                    return None
            elif isinstance(result, list) and len(result) > 0:
                # Handle if response is a list
                first_item = result[0]
                if isinstance(first_item, dict) and "loot_url" in first_item:
                    return first_item["loot_url"]
                else:
                    print(f"Unexpected list response format: {result}")
                    return None
            else:
                print(f"Unexpected response format: {result}")
                return None
                
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            return None
    
    def process_github_script(self, key_content):
        """Process the GitHub script logic with provided key content"""
        # Step 1: Construct the final URL using the key from new.txt
        final_url = f"https://gist.githubusercontent.com/MADNESSTEST/d68fc1ce7ea72159553b21b769a4be1c/raw/{key_content}/key"
        
        # Step 2: Generate LootLabs link
        loot_url = self.generate_lootlabs_link(
            title="Script Key Access",
            final_url=final_url,
            tier_id=1,
            tasks=3,
            theme=3
        )
        
        if loot_url:
            print(f"✅ Generated LootLabs link: {loot_url}")
            print(f"🔗 Original URL: {final_url}")
            print(f"🔑 Key: {key_content}")
            
            # Anti-bypass functionality removed - not needed for this use case
            anti_bypass_url = None
            
            print(f"💾 Saved to secret.txt")
            
            # Save to file
            self.save_link_info(loot_url, final_url, key_content, anti_bypass_url)
            return loot_url
        else:
            print("❌ Failed to generate LootLabs link")
            return None
    
    def save_link_info(self, loot_url, original_url, key, anti_bypass_url=None):
        """Save generated link info to file"""
        # Save just the URL to secret.txt (as requested)
        with open("secret.txt", "w") as f:
            f.write(loot_url)
        
        # Also save detailed info to JSON for reference
        info = {
            "generated_at": datetime.now().isoformat(),
            "loot_url": loot_url,
            "original_url": original_url,
            "key": key,
            "anti_bypass_url": anti_bypass_url
        }
        
        with open("lootlabs_links.json", "w") as f:
            json.dump(info, f, indent=2)

def get_latest_gist_commit_hash(gist_id):
    """Function to get the latest commit hash of a Gist"""
    response = requests.get(f"https://api.github.com/gists/{gist_id}")
    if response.status_code == 200:
        gist = response.json()
        if "history" in gist and gist["history"]:
            latest_commit = gist["history"][0]
            return latest_commit["version"]
    return None

def main():
    # Parse command-line arguments
    if len(sys.argv) < 4:
        print("Usage: python change.py <github_token> <gist_id> <lootlabs_token>")
        sys.exit(1)
    
    github_token = sys.argv[1]
    gist_id = sys.argv[2]
    lootlabs_token = sys.argv[3]

    # Replace these variables with your GitHub username, repository name, and file content
    username = "MADNESSTEST"
    repository_name = "need"
    file_path = "new.txt"

    # Initialize a Github instance with your API token
    g = Github(github_token)

    # Get the repository
    repo = g.get_user(username).get_repo(repository_name)

    # Get the latest commit hash of the Gist
    latest_commit_hash = get_latest_gist_commit_hash(gist_id)

    # Update the content of new.txt with the latest commit hash
    if latest_commit_hash:
        new_file_content = latest_commit_hash
        
        # Check if the file exists and update/create it
        try:
            file = repo.get_contents(file_path)
            # If the file exists, update its content
            repo.update_file(file_path, "Updating file via GitHub Actions", new_file_content, file.sha)
            print("File updated successfully!")
        except:
            # If the file doesn't exist, create it
            repo.create_file(file_path, "Creating file via GitHub Actions", new_file_content)
            print("File created successfully!")
        
        # Now generate the LootLabs link using the updated key
        print("🔄 Generating LootLabs link...")
        loot_generator = LootLabsGenerator(lootlabs_token)
        
        try:
            loot_url = loot_generator.process_github_script(latest_commit_hash)
            
            if loot_url:
                print("✅ LootLabs link generated and saved successfully!")
            else:
                print("❌ Failed to generate LootLabs link")
                # Create empty file so workflow doesn't fail
                with open("secret.txt", "w") as f:
                    f.write("FAILED_TO_GENERATE_LINK")
        except Exception as e:
            print(f"❌ Error generating LootLabs link: {e}")
            # Create empty file so workflow doesn't fail
            with open("secret.txt", "w") as f:
                f.write("ERROR_GENERATING_LINK")
            
    else:
        print("Failed to retrieve latest commit hash of the Gist.")

if __name__ == "__main__":
    main()
