import os
import shutil


# This tool is AI-generated
def purge(dir_path):
    """
    Purge all contents of the specified directory.

    Args:
    dir_path (str): The path to the directory, can be relative or absolute.
    """

    # Convert to absolute path if necessary
    abs_dir_path = os.path.abspath(dir_path)

    # Check if the directory exists
    if os.path.exists(abs_dir_path) and os.path.isdir(abs_dir_path):
        # Remove all the contents of the directory
        for filename in os.listdir(abs_dir_path):
            file_path = os.path.join(abs_dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        print(f"'{abs_dir_path}' does not exist.")
