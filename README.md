# SanityCheck AI 🤖

**AI-Powered Physical Setup Verification for Opentrons Protocols**

SanityCheck AI analyzes Opentrons experimental protocol files (.py), automatically generates checkpoints for physical setup verification, and uses AI (Gemini 2.0) to validate actual setup images, detecting any mistakes before you run your experiments.

---

## 🎯 Key Features

- **Automated Checkpoint Generation**: Automatically generates verification items from protocol files
- **AI-Powered Image Validation**: AI analyzes setup images and validates each checkpoint
- **Intuitive Web UI**: Simple web interface for file upload and result display
- **Detailed Reports**: Shows pass/fail status and detailed explanations for each checkpoint
- **Zero Configuration**: No image preprocessing required - just upload and verify

---

## 📋 System Requirements

- Python 3.10 or higher
- Google AI API Key (Gemini API)
- Internet connection

---

## 🚀 Quick Start

### 1. Clone or Download the Repository

```bash
cd sanitycheckAI
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure your Google AI API Key:

```env
# .env
GOOGLE_API_KEY=your_api_key_here
PORT=8000
```

**How to Get Google AI API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key and paste it into the `.env` file

### 5. Start the Server

```bash
# Method 1: Run as Python module
python -m backend.main

# Method 2: Run directly with Uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Once the server is running, open your browser and navigate to:

```
http://localhost:8000
```

---

## 📖 How to Use

### Basic Usage

1. **Prepare Files**
   - Opentrons protocol file (.py)
   - Photo of your experimental setup (.jpg or .png)

2. **Run Verification**
   - Open http://localhost:8000 in your browser
   - Upload protocol file
   - Upload setup image
   - Click "Start Verification" button

3. **Review Results**
   - Check overall result (Pass/Fail)
   - Review each checkpoint in detail
   - For failed items, check the issue description

### Sample Files

The project includes sample files for testing:

- `96-ch_partial_test.py`: Test protocol file
- `good_photo_1.jpg`: Correct setup example
- `bad_photo_1.jpg`, `bad_photo_2.jpg`, `bad_photo_3.jpg`: Incorrect setup examples

Use these files to verify the system is working correctly.

---

## 🏗️ Project Structure

```
sanitycheckAI/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create yourself)
├── 96-ch_partial_test.py      # Sample protocol
├── good_photo_1.jpg           # Sample image (correct)
├── bad_photo_*.jpg            # Sample images (incorrect)
├── backend/
│   ├── main.py               # FastAPI application
│   ├── gemini_service.py     # Gemini API integration
│   └── prompts.py            # System instruction definitions
├── frontend/
│   ├── index.html            # Main UI
│   ├── style.css             # Styles
│   └── script.js             # Frontend logic
└── docs/
    ├── requirements.md       # Requirements document
    └── QUICKSTART.md         # Quick start guide
```

---

## 🔍 Example Checkpoints

The system automatically checks items such as:

1. ✅ Is the pipette tip rack placed at the specified position (e.g., C2)?
2. ✅ Are all tips filled in the tip rack?
3. ✅ Is the trash bin placed at the specified position (e.g., A3)?
4. ✅ Are there any unnecessary labware in unspecified locations?
5. ✅ Other protocol-specific requirements

---

## 🛠️ Troubleshooting

### Common Issues

**Q: Getting "Google API Key is required" error**
- Check if `.env` file is created correctly
- Verify `GOOGLE_API_KEY` is set correctly
- Confirm the API key is valid

**Q: Cannot upload images**
- Verify file format is .jpg, .jpeg, or .png
- Check file size is not too large (recommended: under 10MB)

**Q: Checkpoints are not generated correctly**
- Confirm protocol file is in Opentrons API 2.x format
- Check for syntax errors in the protocol file

**Q: Cannot access localhost:8000**
- Verify the server is running correctly
- Check if port 8000 is not being used by another application
- Try changing the `PORT` environment variable to use a different port

---

## 🔒 Security Considerations

- **API Key Management**: Never commit the `.env` file to Git
- **Production Use**: Add proper authentication when using in production
- **CORS Settings**: Restrict CORS settings in `backend/main.py` as appropriate

---

## 📝 API Specification

### Endpoints

#### POST /api/validate
Validates protocol and image

**Request:**
- `protocol_file`: Protocol file (.py)
- `image_file`: Setup image (.jpg, .png)

**Response:**
```json
{
  "success": true,
  "checkpoints": [
    {
      "id": 1,
      "description": "Is the pipette tip rack placed at C2?",
      "result": "pass",
      "details": ""
    }
  ],
  "overall_result": "pass"
}
```

#### POST /api/checkpoints
Generates checkpoints only

**Request:**
- `protocol_file`: Protocol file (.py)

**Response:**
```json
{
  "checkpoints": [
    {
      "id": 1,
      "category": "labware_position",
      "description": "Checkpoint description",
      "expected": "Expected state"
    }
  ]
}
```

#### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

---

## 🧪 Testing

### Run API Test Script

```bash
python test_api.py
```

This script allows you to:
1. Test checkpoint generation only
2. Test full verification process (checkpoint generation + image validation)
3. Run both tests

---

## 🔮 Future Enhancements

- Multiple image verification
- Custom checkpoint addition UI
- Verification history storage
- Image annotation (highlighting problem areas)
- Support for other robot platforms
- User authentication
- Database integration
- Multi-language support

---

## 📄 License

This project is released under the MIT License.

---

## 🤝 Contributing

Bug reports, feature requests, and pull requests are welcome!

---

## 📧 Support

If you encounter any issues, please report them in the GitHub Issues section.

---

## 🙏 Acknowledgments

- **Gemini AI** by Google for powerful AI capabilities
- **Opentrons** for their amazing laboratory automation platform
- **FastAPI** for the excellent web framework

---

## ⚠️ Important Notice

This system uses AI (Gemini) for verification and does not guarantee 100% accuracy. **Always perform a final manual check before running important experiments.**

---

**Made with ❤️ for the laboratory automation community**
