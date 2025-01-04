
# Cozy Corner Crew

Cozy Corner Crew is a web application designed to help users analyze and capture the essence of websites by generating moodboards. Whether you're a designer, a developer, or simply a creative enthusiast, this app lets you extract and save inspirations from your favorite websites in a streamlined and organized way.

## **Features**
### Moodboard Creation
- **Website Analysis**: Extract key design elements from a website, including:
  - Fonts used.
  - Color palette.
  - Screenshots of important components.
  - A full-page screenshot of the website.
  
### User Functionality
- **Authentication**: Sign up and log in using:
  - Google
  - GitHub
  - Facebook
- **Moodboard Management**:
  - Save moodboards individually or organize them into collections.
  - Free users can save up to 5 moodboards or collections.
  - Premium users enjoy unlimited moodboards and collections.

### Premium Features
- Stripe integration for premium subscriptions.
- Unlimited saving and organizing capabilities for subscribed users.

## **Tech Stack**
### Backend
- **Framework**: Flask
- **Database**: PostgreSQL
- **Authentication**: OAuth integration with Google, GitHub, and Facebook.
- **Payments**: Stripe for premium feature subscriptions.

### Frontend
- **Technologies**: HTML, CSS, and JavaScript.
- **Libraries**: Utilized various JavaScript libraries for enhanced functionality and responsiveness.

## **Installation and Setup**

### **1. Clone the repository**
```bash
git clone https://github.com/your-username/cozy-corner-crew.git
cd cozy-corner-crew
```

### **2. Set up the environment**
- Create a virtual environment:
  ```bash
  python -m venv venv
  ```
- Activate the virtual environment:
  - On Windows:
    ```bash
    venv\Scripts\activate
    ```
  - On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```

### **3. Install dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set up environment variables**
Create a `.env` file in the project root and define the following variables:
- `FLASK_APP`: The name of your Flask application.
- `FLASK_ENV`: Development or production mode.
- OAuth credentials for Google, GitHub, and Facebook.
- Stripe API keys for payment integration.
- PostgreSQL connection string.

Example:
```env
FLASK_APP=app.py
FLASK_ENV=development
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
FACEBOOK_CLIENT_ID=your_facebook_client_id
FACEBOOK_CLIENT_SECRET=your_facebook_client_secret
STRIPE_SECRET_KEY=your_stripe_secret_key
DATABASE_URL=postgresql://username:password@localhost:5432/cozy_corner
```

### **5. Run the application**
```bash
flask run
```
Visit `http://127.0.0.1:5000` to view the app in your browser.

## **Usage**
1. **Search for a website**: Enter the URL of the website you want to analyze.
2. **View the moodboard**: The app will generate a moodboard displaying fonts, colors, screenshots, and more.
3. **Save or organize**: Save your moodboards individually or group them into collections.
4. **Upgrade to Premium**: Unlock unlimited saving and organizing capabilities.

## **Screenshots**
### Homepage
![Homepage Screenshot](sample/ccc-1.png)

### Moodboard Example
![Moodboard Screenshot](sample/ccc-8.png)

## **Contributing**
Contributions are welcome! Feel free to fork the repository and submit pull requests. 

## **Acknowledgments**
- Flask for the backend framework.
- PostgreSQL for robust database support.
- Stripe for seamless payment integration.
- Flask-Dance for easy OAuth authentication.
- The creative inspiration from countless designers and developers.

Happy Moodboarding! 🌟
