
# TSU CCS Laboratory Web-Management System

## **Authors**
- Sevilla, John Kenneth  
- Suliva, Van Rodolf  
- Yambao, Mark Jonel  

## **Date**  
October 17, 2024

---

## **Table of Contents**
- [Introduction](#introduction)  
- [Technologies Used](#technologies-used)  
- [Features](#features)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Contributing](#contributing)  
- [License](#license)

---

## **Introduction**
The **TSU CCS Laboratory Web-Management System** provides a streamlined web-based solution for managing computer laboratories in Tarlac State University's College of Computer Studies. It addresses key problems like equipment maintenance, issue reporting, and resource management to ensure a seamless learning environment.

---

## **Technologies Used**
- **Backend**: Flask  
- **Database**: MySQL  
- **Frontend**: HTML, CSS, JavaScript, Bootstrap, DataTables  
- **Libraries**: SQLAlchemy, Flask-Login, Flask-Migrate  

---

## **Features**
### **Administrator:**
- User Authentication (Admin and Student roles)  
- CRUD for Rooms and Subjects  
- PC Assignment and Maintenance Management  
- View and Manage Issue Reports  
- Handle Laptop Borrow Requests  

### **Students:**
- View Assigned Lab Classes and PCs  
- Submit Issue Reports  
- Request to Borrow Laptops  

---

## **Installation**
1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/yourusername/tsu-ccs-lab-management.git
   cd tsu-ccs-lab-management
   ```

2. **Create Virtual Environment:**  
   ```bash
   python -m venv venv
   ```

3. **Activate Virtual Environment:**  
   - **Windows:**  
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**  
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment:**  
   Create a `.env` file with:  
   ```env
   FLASK_APP=run.py  
   FLASK_ENV=development  
   SECRET_KEY=your_secret_key  
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@localhost/tsu_ccs_lab
   ```

6. **Initialize Database:**  
   ```bash
   flask db init  
   flask db migrate -m "Initial migration."  
   flask db upgrade
   ```

7. **Run the Application:**  
   ```bash
   flask run
   ```
   Access the application at `http://127.0.0.1:5000/`.

---

## **Usage**
1. **Admin Functionalities:**  
   - Manage Rooms, Subjects, and Assign PCs.  
   - Monitor Issue Reports and Maintenance Logs.  
   - Approve/Deny Laptop Borrow Requests.

2. **Student Functionalities:**  
   - View Dashboard with Lab Classes and PCs.  
   - Submit Issue Reports and Borrow Requests.

---

## **Contributing**
1. Fork the repository.  
2. Create a branch: `git checkout -b feature/YourFeatureName`.  
3. Commit changes: `git commit -m "Add feature"`.  
4. Push to the branch: `git push origin feature/YourFeatureName`.  
5. Open a Pull Request.

---

## **License**
This project is licensed under the [MIT License](LICENSE).

