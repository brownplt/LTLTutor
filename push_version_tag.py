import os
import subprocess

# Filepath to the version file
VERSION_FILE = "src/templates/version.html"

def get_version():
    """Reads the version from the version.html file."""
    try:
        with open(VERSION_FILE, "r") as file:
            version = file.read().strip()
            return version
    except FileNotFoundError:
        print(f"Error: {VERSION_FILE} not found.")
        return None

def create_and_push_tag(version):
    """Creates and pushes a Git tag."""
    tag = f"v{version}"  # Prepend 'v' to the version
    try:
        # Create the tag
        subprocess.run(["git", "tag", "-a", tag, "-m", f"Release {tag}"], check=True)
        print(f"Tag {tag} created successfully.")

        # Push the tag to the remote repository
        subprocess.run(["git", "push", "origin", tag], check=True)
        print(f"Tag {tag} pushed to remote repository.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return False
    return True

def main():
    version = get_version()
    if not version:
        return

    print(f"Version found: {version}")
    if create_and_push_tag(version):
        print("Tagging and pushing completed successfully.")
    else:
        print("Failed to tag and push.")

if __name__ == "__main__":
    main()