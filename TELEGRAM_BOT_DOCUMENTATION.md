# Telegram Bot Integration for Attendance System

## Overview
This system allows schools to set up Telegram bots that automatically link students to their chat IDs when they interact with the bot. Students can send their school name and student code to get registered for attendance notifications.

## How It Works

### 1. Bot Setup Process
1. **Create Telegram Bot**: Use @BotFather to create a new bot and get the token
2. **Configure in Dashboard**: Enter bot token and username in the school admin dashboard
3. **Set Webhook**: Configure webhook URL for receiving messages from Telegram

### 2. Student Registration Methods

#### Method A: Invitation Links (Recommended)
```
1. Admin generates invite link for student: /generate-invite/<student_id>
2. Student clicks link: https://t.me/your_bot?start=ABC123
3. Bot automatically links student's chat ID
4. Student receives confirmation message
```

#### Method B: Manual Registration
```
1. Student sends message to bot: "GREENFIELD ABC123"
2. Bot searches for student with code "ABC123" in school "GREENFIELD"
3. If found, links chat ID and confirms
4. If not found, provides error message with instructions
```

### 3. Notification System
Once linked, students receive:
- **Attendance Notifications**: Absent, present, late status updates
- **School Announcements**: Broadcast messages from administrators
- **Event Reminders**: Important school events and dates

## API Endpoints

### Core Webhook
- `POST /school_admin/webhook/<school_id>` - Receives messages from Telegram

### Configuration
- `GET /school_admin/telegram` - Telegram dashboard page
- `POST /school_admin/telegram-config-api` - Save bot configuration
- `POST /school_admin/setup-webhook/<school_id>` - Set up webhook URL
- `POST /school_admin/test-bot/<config_id>` - Test bot connection

### Student Management
- `GET /school_admin/student-connections` - Get student connection status
- `POST /school_admin/generate-invite/<student_id>` - Generate invite link
- `POST /school_admin/link-student-manual` - Manually link student

### Messaging
- `POST /school_admin/send-attendance-notification` - Send individual notification
- `POST /school_admin/broadcast-message` - Broadcast to all connected students
- `GET /school_admin/bot-status/<school_id>` - Get bot status and statistics

## Database Structure

### TelegramConfig Table
```sql
- id: Primary key
- school_id: Foreign key to schools table
- bot_token: Telegram bot token
- bot_username: Bot username (@your_bot)
- webhook_url: Webhook endpoint URL
- is_active: Boolean status
- created_at/updated_at: Timestamps
```

### Student Table (Extended)
```sql
- telegram_chat_id: Telegram user's chat ID
- telegram_status: Boolean (connected/not connected)
- code: Unique student code for registration
```

## Message Flow Examples

### 1. Student Registration via /start
```
User: /start ABC123
Bot: ✅ Successfully linked! Welcome John Doe.
     You will now receive attendance notifications from Greenfield School.
```

### 2. Manual Registration
```
User: GREENFIELD ABC123
Bot: ✅ Successfully linked! Welcome John Doe.
     🏫 School: Greenfield School
     📚 Grade: Grade 10
     You will now receive attendance notifications.
```

### 3. Attendance Notification
```
Bot: 🔴 ABSENCE NOTIFICATION
     👤 Student: John Doe
     🏫 School: Greenfield School
     📅 Date: October 9, 2025
     
     This is an automated notification from your school's attendance system.
```

### 4. School Announcement
```
Bot: 📢 SCHOOL ANNOUNCEMENT
     👤 Dear John,
     
     Important: School will be closed tomorrow due to weather conditions.
     
     From: Greenfield School
```

## Error Handling

### Invalid Code
```
Bot: ❌ Invalid student code or school. Please check your invitation link and try again.
     If you continue to have issues, please contact your school administrator.
```

### Already Linked
```
Bot: ⚠️ This student code is already linked to another Telegram account.
     Student: John Doe
     If this is your account, please contact your school administrator.
```

### Help Message
```
Bot: 👋 Welcome to Greenfield School Attendance Bot!
     
     To link your account, you can:
     1️⃣ Use invitation link provided by your school
     2️⃣ Manual registration - Send your school name and student code
        Example: 'GREENFIELD ABC123'
     
     📝 Need help? Contact your school administrator.
```

## Implementation Files

1. **telegram_bot.py** - Core bot functionality and message processing
2. **crud_telegram.py** - Flask routes for bot management
3. **telegram_config.html** - Admin dashboard for bot configuration
4. **telegram_bot_examples.py** - Usage examples and documentation

## Security Features

- **School Isolation**: Students can only be linked to their own school's bot
- **Duplicate Prevention**: Prevents multiple accounts from using same student code
- **Session Validation**: All admin actions require proper authentication
- **Error Logging**: Comprehensive logging for debugging and monitoring

## Production Deployment Checklist

1. **HTTPS Setup**: Required for webhook functionality
2. **Domain Configuration**: Update webhook URLs with actual domain
3. **Bot Token Security**: Store bot tokens securely (environment variables)
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Monitoring**: Set up logging and monitoring for bot interactions
6. **Backup Strategy**: Regular backups of student-chat ID mappings

## Usage Statistics Available

- Total students in school
- Connected students (with Telegram)
- Not connected students
- Connection rate percentage
- Bot status and health
- Message delivery statistics

This system provides a complete solution for automated attendance notifications via Telegram, with both user-friendly registration methods and comprehensive administrative controls.