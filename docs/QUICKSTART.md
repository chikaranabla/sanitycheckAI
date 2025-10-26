# Quick Start Guide

This guide explains how to get SanityCheck AI up and running in the fastest way possible.

## ⏱️ Get Started in 5 Minutes

### Step 1: Get Google AI API Key (2 minutes)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated API key (you'll need it later)

### Step 2: Environment Setup (2 minutes)

```bash
# 1. Navigate to project directory
cd sanitycheckAI

# 2. Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Create virtual environment (macOS/Linux)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment variable file
# For Windows
echo GOOGLE_API_KEY=paste_your_api_key_here > .env
echo PORT=8000 >> .env

# For macOS/Linux
echo "GOOGLE_API_KEY=paste_your_api_key_here" > .env
echo "PORT=8000" >> .env
```

**Important**: In the `.env` file, paste the API key you copied in Step 1 after `GOOGLE_API_KEY=`.

### Step 3: Start Server (1 minute)

```bash
# Start the server
python -m backend.main
```

If you see a message like this, you're successful:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 4: Access in Browser

Open the following URL in your browser:

```
http://localhost:8000
```

## 🧪 Test with Sample Files

Use the sample files included in the project to verify the system is working.

### Test with Correct Setup

1. **Protocol File**: Select `96-ch_partial_test.py`
2. **Image File**: Select `good_photo_1.jpg`
3. Click **Start Verification** button

Result: ✅ All checkpoints should pass

### Test with Incorrect Setup

1. **Protocol File**: Select `96-ch_partial_test.py`
2. **Image File**: Select `bad_photo_1.jpg` or `bad_photo_2.jpg`
3. Click **Start Verification** button

Result: ❌ Issues should be detected in some checkpoints

## 📊 Understanding Results

### Overall Judgment

- **✅ Verification Passed**: All checkpoints cleared
- **❌ Verification Failed**: Issues detected in one or more checkpoints

### Checkpoint Details

Each checkpoint displays the following information:

- **Number**: Checkpoint identification number
- **Description**: What is being checked
- **Result**: ✅ (Pass) or ❌ (Fail)
- **Details**: Reason for judgment and additional information

## 🎯 Expected Behavior

### Protocol: `96-ch_partial_test.py`

This protocol expects the following placement:

1. **C2**: 96 Filter Tiprack 1000µL (all tips filled)
2. **A3**: Trash bin
3. **Other positions**: Nothing placed

### For good_photo_1.jpg

- Tip rack correctly placed at C2
- All tips are present
- Trash bin at A3
- Nothing placed in unnecessary locations

→ **Result**: ✅ All pass

### For bad_photo_*.jpg

Contains various issues:

- Missing tips
- Wrong position
- Unnecessary items placed

→ **Result**: ❌ Issues detected

## 🔧 Troubleshooting

### Server Won't Start

```bash
# Check error message
python -m backend.main
```

**Common Causes:**
- `.env` file not created
- API key not set
- Port 8000 already in use

**Solution:**
```bash
# Check .env file
cat .env  # macOS/Linux
type .env  # Windows

# Use different port
# Change PORT=8001 in .env file
```

### "Google API Key is required" Error

Check your `.env` file:

```env
GOOGLE_API_KEY=actual_api_key
PORT=8000
```

Verify the API key is set correctly with no extra spaces or line breaks.

### Page Doesn't Display in Browser

1. Verify server is running
2. Check URL is correct: `http://localhost:8000`
3. Try a different browser
4. Clear cache

### Verification is Slow

Gemini API calls can take time (10-30 seconds).
Ensure your network connection is stable.

## 🎓 Next Steps

Once the system is working properly, try these:

1. **Test with Your Own Protocol Files**
   - Upload your Opentrons experimental protocol
   - Validate with actual setup photos

2. **Use API Directly**
   - Call `/api/validate` endpoint with cURL or Python
   - Integrate into automation scripts

3. **Customize Code**
   - Adjust checkpoints in `backend/prompts.py`
   - Customize UI in `frontend/`

## 📚 More Information

For more detailed information, refer to these documents:

- [README.md](../README.md): Complete documentation
- [requirements.md](requirements.md): Requirements document
- [FastAPI Documentation](http://localhost:8000/docs): API detailed specifications (access after server starts)

## 💡 Tips

- **Taking Photos**: Shoot from directly above so the entire deck is visible - improves AI judgment accuracy
- **Writing Protocols**: Clearly specify positions in load_labware() and load_trash_bin()
- **Interpreting Results**: AI judgment is for reference. Always perform final human verification

---

**If problems persist, please ask questions in GitHub Issues.**
