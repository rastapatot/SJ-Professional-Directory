#!/bin/bash
# SJ Professional Directory - Local Deployment Script
# ============================================================================

echo "🏢 SJ Professional Directory - Local Deployment"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found. Please run from the SJ directory."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python: $python_version"

# Check if database exists
if [ ! -f "sj_directory.db" ]; then
    echo "🗄️  Database not found. Creating database..."
    python3 run.py --create-db
    if [ $? -ne 0 ]; then
        echo "❌ Database creation failed!"
        exit 1
    fi
fi

# Check if data has been imported
db_size=$(sqlite3 sj_directory.db "SELECT COUNT(*) FROM members;" 2>/dev/null || echo "0")
if [ "$db_size" -eq "0" ]; then
    echo "📥 No data found. Importing from Raw_Files..."
    python3 run.py --import
    if [ $? -ne 0 ]; then
        echo "⚠️  Data import had issues, but continuing..."
    fi
fi

echo "📊 Database contains $db_size members"

# Install required packages if missing
echo "📦 Checking dependencies..."
python3 -c "import streamlit, pandas, fuzzywuzzy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing missing dependencies..."
    pip3 install streamlit pandas fuzzywuzzy python-levenshtein xlrd openpyxl chardet
fi

# Create logs directory
mkdir -p logs

echo ""
echo "🚀 Starting SJ Professional Directory..."
echo "📍 Local URL: http://localhost:8501"
echo "🔒 Admin Password: SJ92C!"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"

# Start Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.address localhost