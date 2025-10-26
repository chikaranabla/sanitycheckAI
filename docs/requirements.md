# SanityCheck AI - Requirements Document

## 1. Project Overview

SanityCheck AI analyzes Opentrons experimental protocol files (.py), automatically generates checkpoints for physical setup verification, and uses AI to validate actual setup images, detecting any mistakes.

## 2. System Architecture

```
[Frontend (Web UI)]
    ↓ File Upload (.py + 1 image)
[Backend (FastAPI)]
    ↓ API Call
[Gemini 2.0 API]
  - Phase 1: Protocol Analysis → Checkpoint Generation
  - Phase 2: Image Validation → Pass/Fail Judgment
    ↓ Return Results
[Frontend]
  - Display Checkpoints and Results
```

## 3. Functional Requirements

### 3.1 File Upload Function

- Upload Opentrons protocol file (.py)
- Upload setup image (jpg/png) - 1 image
- File format validation

### 3.2 Checkpoint Generation Function (Gemini API Phase 1)

- Analyze protocol file
- Generate checkpoints for physical setup verification
- Checkpoint examples:
    - Is pipette tip rack at C2?
    - Are all pipette tips filled in C2?
    - Are there unnecessary items in unwanted locations?
    - Other protocol-specific requirements

### 3.3 Image Validation Function (Gemini API Phase 2)

- Validate image based on generated checkpoints
- Judge pass (○) or fail (×) for each checkpoint
- Provide reasons for failed items

### 3.4 Result Display Function

- Display checkpoint list
- Display judgment result (○×) for each item
- Overall judgment (all passed/failed)
- Detailed explanation for failed items

## 4. Technology Stack

### Frontend

- HTML/CSS/JavaScript (Simple UI)
- React/Vue.js (for future expansion if needed)

### Backend

- Python 3.10+
- FastAPI (Web API Framework)
- Google Generative AI SDK (Gemini API)
- Uvicorn (ASGI Server)

### Other

- dotenv (Environment variable management)
- Pillow (Image processing, if needed)

## 5. Processing Flow

### 5.1 Overall Flow

1. User uploads protocol file (.py) and image via Web UI
2. Backend receives files
3. Send System Prompt and protocol file to Gemini API (Phase 1)
4. Gemini generates checkpoints (returns in JSON format)
5. Send image to same session (context maintained) (Phase 2)
6. Gemini validates each checkpoint and returns results (in JSON format)
7. Backend formats results and returns to frontend
8. Display verification results in UI

### 5.2 Gemini API Call Details

**Phase 1: Checkpoint Generation**

- System Instruction: Instructions for protocol analysis and checkpoint generation
- Input: Protocol file content (text)
- Output: Checkpoint list (JSON)

**Phase 2: Image Validation**

- Same chat session (context continued)
- Input: Setup image
- Output: Verification results for each checkpoint (JSON)

## 6. Checkpoint Definition (Include in System Instruction)

Default checkpoint examples:

1. Is pipette tip rack placed at C2?
2. Are all pipette tips properly filled in C2?
3. Is trash bin placed at A3?
4. Are there unnecessary labware in unspecified locations?
5. Are other labware specified in the protocol at correct positions?

**Important: Do NOT include deck offset settings (set_offset) in checkpoints - these are software configurations.**

## 7. Input/Output Specification

### 7.1 API Input

- Protocol file: `.py` format (multipart/form-data)
- Image file: `.jpg` or `.png` (multipart/form-data)

### 7.2 API Output (JSON)

```json
{
  "success": true,
  "checkpoints": [
    {
      "id": 1,
      "description": "Is pipette tip rack placed at C2?",
      "result": "pass",
      "details": ""
    },
    {
      "id": 2,
      "description": "Are all pipette tips properly filled in C2?",
      "result": "fail",
      "details": "Missing tips in the bottom left area"
    }
  ],
  "overall_result": "fail"
}
```

### 7.3 UI Display

- Checkpoint list (number, description, result icon)
- Overall judgment (prominently displayed)
- Detailed explanation for failed items

## 8. File Structure

```
sanitycheckAI/
├── README.md              # System description, setup instructions
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create yourself)
├── backend/
│   ├── main.py           # FastAPI application
│   ├── gemini_service.py # Gemini API integration
│   └── prompts.py        # System instruction definitions
├── frontend/
│   ├── index.html        # Main UI
│   ├── style.css         # Styles
│   └── script.js         # Frontend logic
└── docs/
    ├── requirements.md   # This requirements document
    └── QUICKSTART.md     # Quick start guide
```

## 9. Implementation Priority

1. Requirements document creation (this document)
2. Backend API implementation (FastAPI + Gemini API integration)
3. System Instruction & Prompt design
4. Frontend UI implementation
5. Integration testing (verify with good_photo_1.jpg, bad_photo_*.jpg)
6. Documentation improvement

## 10. Constraints and Prerequisites

- No image preprocessing (pass directly to Gemini API)
- Only 1 image per verification
- Gemini API key required
- Internet connection required
- Protocol file must be in Opentrons API 2.x format

## 11. Future Enhancement Possibilities

- Multiple image verification
- Custom checkpoint addition UI
- Verification history storage
- Image annotation (highlighting problem areas)
- Support for other robot platforms
- User authentication
- Database integration
