# Travel Packer

A simple, functional web application to manage your travel checklists and ensure you never forget anything (summer items, winter items, pet requirements, etc.).

Test me! https://663260932.xyz/travelpacker

## Features
- **No passwords required:** Login using a simple Alias.
- **Guest Mode:** Try it out without saving permanent data (wiped after 24 hours).
- **Customizable:** Pre-filled default categories. Users can also create their own categories and items.
- **Admin Panel:** An administrator can manage the global defaults.
- **Multilingual:** Supports English and Spanish out-of-the-box.
- **Dynamic Checklists:** 4 states per item (To Pack, Packed, N/A, Standby) + custom notes. Saves automatically.

## Installation

1. **Clone the repository or download the folder.**
2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
4. **Run the application:**
    ```bash
    python app.py

    The database (database.db) will be created and seeded automatically on the first run.

    Access the App: Open http://127.0.0.1:5000 in your browser.

## Administration

To access the Admin panel and manage the default (global) items and categories, simply log in with the alias admin.

