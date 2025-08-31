# 🏠 Local Deployment Guide

## Quick Start (Your app is already running!)

Your SJ Professional Directory is currently running at:
**http://localhost:8501**

- 🔍 **Search for professionals**: "I need a lawyer in Makati"
- 📋 **Browse directory**: Search by name, batch, chapter
- ⚙️ **Admin access**: Password is `SJ92C!`

## 🚀 Easy Deployment Options

### Option 1: One-Click Scripts

**Bash script (Mac/Linux):**
```bash
./deploy_local.sh
```

**Python script (Cross-platform):**
```bash
python3 deploy_local.py
```

### Option 2: Manual Commands

**Basic startup:**
```bash
streamlit run streamlit_app.py
```

**With specific port:**
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Option 3: Using run.py

```bash
python3 run.py              # Starts Streamlit
python3 run.py --flask      # Alternative Flask interface
```

## 📊 Your Current System Status

✅ **Database**: `sj_directory.db` with 2,804+ members
✅ **Data Imported**: All Raw_Files processed successfully  
✅ **Search Working**: Professional services matching active
✅ **Admin Protected**: Password-secured admin panel
✅ **All Dependencies**: Installed and working

## 🔧 System Information

- **URL**: http://localhost:8501
- **Admin Password**: `SJ92C!`
- **Database**: SQLite (sj_directory.db)
- **Members**: 2,804+ imported from Raw_Files
- **Features**: AI-powered search, duplicate detection, audit trails

## 🌐 Network Access (Optional)

To share with others on your network:

```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Then share: `http://YOUR_LOCAL_IP:8501`

## 🛠️ Troubleshooting

**If app won't start:**
```bash
# Check dependencies
python3 -c "import streamlit, pandas, fuzzywuzzy"

# Install missing packages
pip3 install streamlit pandas fuzzywuzzy python-levenshtein xlrd openpyxl

# Recreate database
python3 run.py --create-db
python3 run.py --import
```

**If search not working:**
- Check admin panel for data quality metrics
- Try different query formats
- Verify database has members with professions

**Common Issues:**
- Port 8501 already in use → Try different port
- Permission errors → Use `pip3 install --user`
- Database locked → Close other connections

## 📱 Usage Examples

**Professional Services:**
- "I need a family lawyer in Bulacan"
- "Find doctors in Heart Center"
- "Do we have engineers in Makati?"

**Directory Search:**
- Name: "Juan Dela Cruz"
- Batch: "95-S"
- Chapter: "UP Diliman"
- Profession: "Lawyer"

## 🔒 Security

- Admin panel protected with password
- Local-only access by default
- No external data transmission
- Complete data privacy

Your professional directory is ready to replace group chat queries! 🎯