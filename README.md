# EduTrack360 🎓

A comprehensive school management system built with Flask, featuring modern UI design and advanced functionality for educational institutions.

## ✨ Features

### 🎨 **Modern Dark Blue Theme**
- Sophisticated dark blue color palette throughout the application
- Glass morphism effects and backdrop blur designs
- Advanced CSS animations and interactive elements
- Fully responsive design for all devices

### 👥 **Multi-Role System**
- **Main Admin**: System-wide management and oversight
- **School Admin**: School-specific administration
- **Instructor**: Course and attendance management
- **Student**: Access to academic information

### 📊 **Core Functionality**
- **Attendance Management**: Real-time attendance tracking
- **Section Management**: Class organization and management
- **Instructor Management**: Faculty administration
- **Student Management**: Student information system
- **Subject Management**: Curriculum organization
- **Notification System**: Automated alerts and updates

### 🚀 **Advanced UI Features**
- **Animated Landing Page**: Hero section with particle effects
- **Interactive Navigation**: Smooth scrolling and responsive menus
- **Modal Systems**: Enhanced authentication and form dialogs
- **Typewriter Effects**: Dynamic text animations
- **Scroll Reveal**: Progressive content revelation
- **Hover Animations**: Interactive card effects and transitions

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Tailwind CSS with custom components
- **Authentication**: Flask session management
- **Icons**: Font Awesome

## 📁 Project Structure

```
dexter_project/
├── app.py                          # Main Flask application
├── models.py                       # Database models
├── helpers.py                      # Utility functions
├── instance/
│   └── config.py                   # Configuration settings
├── blueprints/
│   ├── auth/                       # Authentication routes
│   ├── main_admin/                 # Main admin functionality
│   ├── school_admin/               # School admin features
│   └── instructor/                 # Instructor dashboard
└── templates/
    ├── landing.html                # Modern landing page
    ├── login.html                  # Authentication forms
    ├── main_admin/                 # Main admin templates
    ├── school_admin/               # School admin templates
    └── instructor/                 # Instructor templates
```

## 🎨 Design Highlights

### **Landing Page**
- Hero section with animated gradients
- Particle system background effects
- Typewriter text animations
- Interactive feature cards
- Modern contact forms

### **Dashboard Interfaces**
- Dark blue theme with gradient backgrounds
- Card-based layouts with hover effects
- Glass morphism navigation bars
- Responsive grid systems
- Enhanced modal designs

### **Form Components**
- Backdrop blur effects
- Smooth transitions and animations
- Interactive button states
- Loading indicators
- Success/error feedback

## 🚀 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/keiji0711/solo_project.git
   cd solo_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-mysqldb
   ```

4. **Configure database**
   - Update `instance/config.py` with your MySQL credentials
   - Create the database tables

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser to `http://localhost:5000`

## 🎯 Key Features Showcase

### **Responsive Design**
- Mobile-first approach
- Breakpoint-specific optimizations
- Touch-friendly interface
- Dynamic scaling

### **Advanced Animations**
- CSS keyframe animations
- JavaScript scroll effects
- Interactive hover states
- Loading transitions

### **Modern UI Patterns**
- Glass morphism effects
- Gradient backgrounds
- Shadow depth systems
- Typography hierarchy

## 🔧 Customization

The application uses CSS custom properties for easy theme customization:

```css
:root {
  --primary-dark: #1e3a8a;
  --primary: #2563eb;
  --primary-light: #3b82f6;
}
```

## 📱 Browser Support

- Chrome 70+
- Firefox 65+
- Safari 12+
- Edge 79+

## 👨‍💻 Developer

**Dexter** - Full-stack developer specializing in modern web applications

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🚀 Future Enhancements

- Real-time notifications
- Advanced reporting system
- Mobile application
- API endpoints
- Enhanced security features

---

Built with ❤️ using Flask and modern web technologies
# EduTrack360
