# SJ Professional Directory

A comprehensive, AI-powered professional directory system for fraternity members, designed to replace group chat queries with intelligent professional services matching.

## 🎯 Purpose

Transform how fraternity members find professional help by:
- **Natural Language Queries**: "I need a family lawyer in Bulacan" → Get relevant member matches
- **Professional Services Matching**: AI-powered profession inference and location matching
- **Complete Member Directory**: Searchable database with contact information and professional details
- **Data Quality Management**: Automatic duplicate detection, data normalization, and change tracking

## 🚀 Features

### Core Functionality
- **Natural Language Processing**: Query in plain English for professional services
- **AI-Powered Inference**: Automatically detect professions from email domains, company names, addresses
- **Smart Data Normalization**: Handle name variations, batch number formats, location aliases
- **Duplicate Detection**: Intelligent merging of duplicate member records
- **Comprehensive Audit Trail**: Track all data changes with timestamps and sources

### Professional Services Matching
- **Query Examples**:
  - "I need a family lawyer in Bulacan"
  - "Do we have a cardiologist at Heart Center?"
  - "Find accountants in Makati CBD"
  - "Show me engineers from batch 95-S"

### Data Sources Supported
- **Excel Files** (.xls, .xlsx): Member directories and contact lists
- **Word Documents** (.doc, .docx): Structured member profiles
- **Access Databases** (.mdb): Existing member databases
- **Text Files** (.txt): Email lists and simple data
- **CSV Files**: Exported member data

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Git (optional, for cloning)

### Quick Setup

1. **Clone or download the project**:
   ```bash
   git clone <repository-url>
   cd SJ
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data**:
   - Place all member data files in the `Raw_Files/` directory
   - Supported formats: .xls, .xlsx, .doc, .docx, .mdb, .txt, .csv

4. **Initialize the system**:
   ```bash
   python run.py --create-db    # Create database
   python run.py --test         # Verify system works
   python run.py --import       # Import your data
   ```

5. **Start the application**:
   ```bash
   python run.py
   ```

6. **Access the directory**:
   - Open your browser to `http://localhost:5000`
   - Start querying: "I need a lawyer in Manila"

## 📁 Project Structure

```
SJ/
├── Raw_Files/                  # Your member data files
│   ├── members.xls
│   ├── directory.doc
│   ├── UP Chapters/
│   └── Other Chapters/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── database.py                 # Database operations
├── data_processor.py           # Data import and normalization
├── text_processor.py           # Text processing and normalization
├── ai_inference.py            # AI-powered profession inference
├── query_processor.py          # Natural language query processing
├── database_schema.sql         # Complete database schema
├── requirements.txt            # Python dependencies
├── run.py                     # Quick run script
├── test_system.py             # System tests
└── README.md                  # This file
```

## 🔧 Usage

### Command Line Interface

```bash
# Start the Streamlit web application (default)
python run.py

# Start the Flask web application (alternative)
python run.py --flask

# Run system tests
python run.py --test

# Import data from Raw_Files directory
python run.py --import

# Create database only
python run.py --create-db

# Direct Streamlit launch
streamlit run streamlit_app.py
```

### Streamlit Web Interface

1. **🔍 Professional Services Tab**: 
   - Ask natural language questions: "I need a lawyer in Makati"
   - Get ranked results with confidence scores
   - See why each person matches your query

2. **📋 Directory Search Tab**: 
   - Traditional member lookup by name, batch, chapter
   - Interactive data table with clickable rows
   - Detailed member profiles on selection

3. **⚙️ Admin Panel**: 
   - Import data from Raw_Files directory
   - Upload new files directly
   - Monitor data quality metrics
   - Find and merge duplicate records

4. **ℹ️ About Page**: 
   - Usage instructions and examples
   - System information and statistics

### Query Examples

**Professional Services**:
- "I need a family lawyer in Bulacan"
- "Find doctors specializing in cardiology"
- "Do we have any accountants in BGC?"
- "Looking for civil engineers in Quezon City"

**Directory Searches**:
- "Find Juan Dela Cruz"
- "Show me batch 95-S members"
- "List all UP Diliman brothers"
- "Members from Iloilo chapter"

## 🧠 AI Features

### Profession Inference
The system automatically infers member professions from:
- **Email domains**: `@hospital.com` → Medical profession
- **Company names**: "Law Office" → Legal profession
- **Job titles**: "Software Engineer" → IT/Technology
- **Office addresses**: "Medical Center" → Healthcare

### Smart Normalization
- **Names**: "Dr. Juan Dela Cruz Jr." → "juan dela cruz"
- **Batches**: "Batch 95-S" → "1995-S"
- **Locations**: "QC" → "Quezon City"
- **Addresses**: Separate home vs. office addresses

### Query Understanding
Natural language processing to understand:
- **Intent**: Professional service vs. directory search
- **Profession**: Legal, medical, engineering, business
- **Location**: Cities, regions, specific areas
- **Urgency**: Regular vs. urgent requests

## 📊 Data Quality

### Automatic Features
- **Duplicate Detection**: Find similar names and identical emails
- **Data Completeness Scoring**: Rate record quality (0-100%)
- **Confidence Scoring**: AI confidence in inferences
- **Data Vintage Tracking**: Know how old information is

### Manual Management
- **Merge Duplicates**: Combine duplicate records intelligently
- **Verify Information**: Mark data as verified or outdated
- **Add Missing Data**: Fill gaps in member information
- **Quality Reports**: Monitor data health

## 🔒 Privacy & Security

- **Local Database**: All data stays on your system
- **No External APIs**: No data sent to third parties (unless using OpenAI features)
- **Audit Trails**: Complete history of all data changes
- **Access Control**: Web interface can be password-protected

## 🚀 Deployment Options

### Local Use
- Run on personal computer
- Access via `localhost:8501` (Streamlit) or `localhost:5000` (Flask)

### Streamlit Cloud (Free Hosting)
1. Push your code to GitHub
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Deploy with one click
4. Share the URL with members

### Network Sharing
- Run on shared computer/server
- Access from other devices on network: `http://[server-ip]:8501`
- Configure firewall as needed

### Portable Distribution
- Package as single executable with PyInstaller
- Distribute to members
- No installation required

## 🛠️ Configuration

Edit `config.py` to customize:
- **Database location**
- **AI inference settings**
- **Professional categories**
- **Location mappings**
- **Batch normalization rules**

## 📈 Monitoring

The system provides:
- **Import Statistics**: Track data import success/failures
- **Query Analytics**: Monitor most common searches
- **Data Quality Metrics**: Completeness and confidence scores
- **System Health**: Database status and performance

## 🤝 Contributing

To extend the system:
1. **Add new profession categories** in `config.py`
2. **Customize query patterns** in `query_processor.py`
3. **Add new data sources** in `data_processor.py`
4. **Improve AI inference** in `ai_inference.py`

## 📝 Database Schema

The system uses a comprehensive SQLite database with:
- **Members table**: Core member information with normalization
- **Change history**: Complete audit trail of all changes
- **Import tracking**: Monitor data import batches
- **Duplicate management**: Handle and merge duplicate records
- **Professional services**: Service categories and availability

See `database_schema.sql` for complete schema details.

## ❓ Troubleshooting

### Common Issues

**Import Errors**:
- Check file formats are supported
- Verify Raw_Files directory exists
- Run `python run.py --test` to diagnose

**Search Not Working**:
- Ensure data was imported successfully
- Check database was created
- Verify query format

**Performance Issues**:
- Large datasets may need indexing optimization
- Consider batch processing for imports
- Monitor database size

### Getting Help

1. Run system tests: `python run.py --test`
2. Check logs in `logs/` directory
3. Verify configuration in `config.py`
4. Review database schema for data structure

## 📄 License

This project is designed for fraternity use. Modify and distribute as needed for your organization.

---

**Built with ❤️ for stronger fraternal connections**