import os
import re
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def update_mongodb_connection(connection_string=None):
    """
    Update the MongoDB connection string in config.py

    Args:
        connection_string: The new MongoDB connection string
    """
    if connection_string is None:
        # Use environment variable or default placeholder
        connection_string = os.environ.get('MONGODB_URI', 'mongodb+srv://[username]:[password]@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority')
        
    # Validate the connection string
    if not connection_string.startswith('mongodb'):
        logging.error("Invalid MongoDB connection string. It should start with 'mongodb'")
        return False

    # Update config.py
    config_path = 'config.py'
    if not os.path.exists(config_path):
        logging.error(f"{config_path} not found")
        return False

    try:
        with open(config_path, 'r') as f:
            content = f.read()

        # Replace the connection string
        pattern = r"MONGODB_URI = os\.environ\.get\('MONGODB_URI', '[^']*'\)"
        replacement = f"MONGODB_URI = os.environ.get('MONGODB_URI', '{connection_string}')"

        if re.search(pattern, content):
            updated_content = re.sub(pattern, replacement, content)

            with open(config_path, 'w') as f:
                f.write(updated_content)

            logging.info(f"Updated MongoDB connection string in {config_path}")
            return True
        else:
            logging.warning(f"Could not find MongoDB connection string pattern in {config_path}")
            
            # Try a different pattern
            pattern = r"MONGODB_URI\s*=\s*'[^']*'"
            if re.search(pattern, content):
                updated_content = re.sub(pattern, f"MONGODB_URI = '{connection_string}'", content)
                
                with open(config_path, 'w') as f:
                    f.write(updated_content)
                
                logging.info(f"Updated MongoDB connection string in {config_path} (alternative pattern)")
                return True
            else:
                logging.error(f"Could not find any MongoDB connection string pattern in {config_path}")
                return False
    except Exception as e:
        logging.error(f"Error updating {config_path}: {e}")
        return False

def update_mongodb_uri_in_all_files(directory='.'):
    """
    Update MongoDB connection strings in all Python files in the given directory.
    """
    # Use environment variables or default placeholders
    ATLAS_MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://[username]:[password]@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority')
    ATLAS_MONGODB_TEST_URI = os.environ.get('MONGODB_TEST_URI', 'mongodb+srv://[username]:[password]@cluster0.qrrpagr.mongodb.net/remotehive_test?retryWrites=true&w=majority')
    
    updated_files = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Skip files that are too large (likely binary or generated files)
                    if len(content) > 1000000:  # Skip files larger than 1MB
                        logging.warning(f"Skipping large file: {filepath}")
                        continue
                    
                    original_content = content
                    
                    # Replace MongoDB URIs with Atlas URIs
                    # Pattern 1: Direct string assignments
                    content = re.sub(
                        r"'mongodb://localhost:27017/remotehive'",
                        f"'{ATLAS_MONGODB_URI}'",
                        content
                    )
                    content = re.sub(
                        r"'mongodb://localhost:27017/remotehive_test'",
                        f"'{ATLAS_MONGODB_TEST_URI}'",
                        content
                    )
                    
                    # Pattern 2: In connect() calls
                    content = re.sub(
                        r'host="mongodb://localhost:27017/remotehive"',
                        f'host="{ATLAS_MONGODB_URI}"',
                        content
                    )
                    content = re.sub(
                        r'host="mongodb://localhost:27017/remotehive_test"',
                        f'host="{ATLAS_MONGODB_TEST_URI}"',
                        content
                    )
                    
                    # Pattern 3: With single quotes in connect() calls
                    content = re.sub(
                        r"host='mongodb://localhost:27017/remotehive'",
                        f"host='{ATLAS_MONGODB_URI}'",
                        content
                    )
                    content = re.sub(
                        r"host='mongodb://localhost:27017/remotehive_test'",
                        f"host='{ATLAS_MONGODB_TEST_URI}'",
                        content
                    )
                    
                    # Pattern 4: With variable names
                    content = re.sub(
                        r"MONGODB_URI\s*=\s*'mongodb://localhost:27017/remotehive'",
                        f"MONGODB_URI = '{ATLAS_MONGODB_URI}'",
                        content
                    )
                    content = re.sub(
                        r"MONGODB_URI\s*=\s*'mongodb://localhost:27017/remotehive_test'",
                        f"MONGODB_URI = '{ATLAS_MONGODB_TEST_URI}'",
                        content
                    )
                    
                    # Write the file only if changes were made
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        logging.info(f"Updated MongoDB connection strings in {filepath}")
                        updated_files += 1
                except Exception as e:
                    logging.error(f"Error processing file {filepath}: {e}")
    
    return updated_files

if __name__ == "__main__":
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
        success = update_mongodb_connection(connection_string)
    else:
        # Update MongoDB URIs in the current directory and all subdirectories
        updated_files = update_mongodb_uri_in_all_files('.')
        logging.info(f"Updated MongoDB connection strings in {updated_files} files")
        
        # Also update the config.py file
        success = update_mongodb_connection()
        
    if success:
        logging.info("MongoDB connection string updated successfully!")
        logging.info("You can now run the application with: python app.py")
    else:
        logging.error("Failed to update MongoDB connection string in config.py.")
        # Don't exit with error code as we may have updated other files successfully
