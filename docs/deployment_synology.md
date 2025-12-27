# Deploying to Synology NAS

This guide explains how to run the application on your Synology NAS using **Container Manager** (formerly Docker).

## Prerequisites

1.  **Synology NAS** with DSM 7.2 or later recommended.
2.  **Container Manager** package installed from the Package Center.
3.  SSH access (optional, but helpful) or File Station access.

## Step 1: Prepare the Project

Before uploading, it is recommended to create a clean zip of the project excluding large local directories (`venv`, `node_modules`, `.git`).

1.  Open your terminal in the project root.
2.  Create a zip file (Mac/Linux):
    ```bash
    zip -r bga-nas.zip . -x "*.git*" "*/node_modules/*" "*/.venv/*" "*/__pycache__/*"
    ```
    *If you prefer manually*, just copy the folder and delete `node_modules` and `.venv` before zipping.

## Step 2: Upload to NAS

1.  Log in to your Synology DSM.
2.  Open **File Station**.
3.  Create a folder for the project, e.g., `/docker/bga`.
4.  Upload `bga-nas.zip` to that folder.
5.  Right-click the zip file and select **Extract Here**.

## Step 3: Configure Container Manager

1.  Open **Container Manager**.
2.  Go to **Project** tab.
3.  Click **Create**.
4.  **Project Name**: `bga` (or whatever you prefer).
5.  **Path**: Browse and select the folder where you extracted the files (e.g., `/docker/bga`).
6.  **Source**: Select **Create docker-compose.yml**.
    *   *Wait!* We already have a file.
    *   Instead, since we have `docker-compose.nas.yml`, we can select **Use existing docker-compose.yml** if the option is available for the selected path.
    *   **Alternative**: If Container Manager forces you to use `docker-compose.yml`:
        1.  In File Station, rename `docker-compose.nas.yml` to `docker-compose.yml`. (You can rename the original one to `docker-compose.dev.yml` or overwrite it).
        2.  Then in Container Manager, it will detect the file.

    **Recommended Approach:**
    1.  Go to File Station.
    2.  Rename `docker-compose.yml` -> `docker-compose.local.yml`.
    3.  Rename `docker-compose.nas.yml` -> `docker-compose.yml`.
    4.  Back in Container Manager -> Create Project -> Path: `/docker/bga` -> It should ask "Use existing docker-compose.yml?". Say **Yes**.

## Step 4: Build and Run

1.  Follow the wizard in Container Manager.
2.  Enable **Web portal** via Web Station if you want a custom domain (optional), or just use the port.
3.  Click **Done**.
4.  Container Manager will start building the images (downloading Python, Node, etc.). *This may take 10-20 minutes depending on your NAS speed.*
5.  Once Status is **Running (Green)**, you are good to go.

## Step 5: Access the App

-   **Frontend**: `http://<YOUR_NAS_IP>:3001`
-   **Backend**: `http://<YOUR_NAS_IP>:8000`

### Data Persistence
The database files will be stored in a folder named `db_data` inside your project folder on the NAS. This ensures that your data remains safe even if you delete the containers or the project configuration. You can easily back up this folder.

## Updates

To update the code:
1.  Upload new files.
2.  In Container Manager -> Project -> Select `bga` -> Action -> **Build** (or specific Rebuild option).
