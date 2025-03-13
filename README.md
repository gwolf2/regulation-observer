# Regulation Observer

Regulation Observer is a tool designed to process and extract specific sections from XML files containing regulatory documents. The tool parses filenames to determine the sections to extract and processes the XML content to keep only the most specific section, overwriting the original file with the extracted content.

## Features

- Parse filenames to extract Title, Subtitle, Chapter, and Subchapter information.
- Count words in the content.
- Find and extract specific sections (Subtitle, Chapter, Subchapter) from XML files.
- Process all XML files in a directory and its subdirectories.
- Maintain a basic XML structure in the processed files.

## Usage

1. Place your XML files in the `data` directory.
2. Run the script to process the files:

    ```sh
    python extract_extra_sections.py
    ```

3. The script will process each XML file, extract the desired section, and overwrite the original file with the extracted content.

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/regulation-observer.git
    ```

2. Navigate to the project directory:

    ```sh
    cd regulation-observer
    ```

3. Ensure you have Python installed on your system.

## Configuration

To ensure the `data` directory is not pushed to the remote repository, the `.gitignore` file includes the following entry:

```plaintext
# Ignore the data directory
data/
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.