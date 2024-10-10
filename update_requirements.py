import subprocess
import sys

def update_requirements():
    # Get the output of pip freeze
    result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    requirements = result.stdout.split('\n')

    # Filter out the line with git+ssh
    filtered_requirements = [req for req in requirements if not req.startswith('-e git+ssh')]

    # Add the local editable install
    filtered_requirements.append('-e .')

    # Write the filtered requirements to requirements.txt
    comment = "# To update this file, run: python update_requirements.py\n\n"
    with open('requirements.txt', 'w') as f:
        f.write(comment)
        f.write('\n'.join(filtered_requirements))

    print("requirements.txt has been updated.")

if __name__ == "__main__":
    update_requirements()
