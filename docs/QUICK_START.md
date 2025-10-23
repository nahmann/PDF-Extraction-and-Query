# Quick Start Guide

## First Time Setup

```bash
# 1. Start Docker Desktop (if not running)
# Look for Docker whale icon in system tray

# 2. Start database
cd database
docker-compose up -d
cd ..

# 3. Upload all PDFs (490 files - takes ~10-15 minutes)
python test_interactive_search.py --folder "tests/fixtures/sample_pdfs/deepshield-systems-inc"
```

## Daily Usage

```bash
# Query documents (skip upload)
python test_interactive_search.py --skip-upload
```

Then type your questions:
```
Query: What are the vesting terms?
Query: Tell me about the security policies
Query: What are the board governance rules?
```

## Useful Commands

### Database Management
```bash
# See stats
python scripts/manage_database.py --stats

# Clear everything (fresh start)
python scripts/manage_database.py --clear

# List documents
python scripts/list_documents.py
```

### Testing Different Folders
```bash
# Use default (subset_pdfs - 4 files)
python test_interactive_search.py

# Use full set (490 files)
python test_interactive_search.py --folder "tests/fixtures/sample_pdfs/deepshield-systems-inc"

# Use your own folder
python test_interactive_search.py --folder "path/to/your/pdfs"
```

### Interactive Commands

Once in query mode:
- `list` - Show all uploaded documents
- `top 5` - Change number of results
- `chunk <doc_id> <num>` - View full chunk text
- `quit` - Exit

## Key Features

✅ **Recursive Upload** - Finds PDFs in all subdirectories
✅ **Duplicate Detection** - Won't re-upload same files
✅ **Full Paths** - Shows folder structure in results
✅ **Smart Search** - Semantic similarity across all documents

## Typical Workflow

```bash
# Monday: Upload new documents
python scripts/manage_database.py --clear
python test_interactive_search.py --folder "path/to/pdfs"

# Tuesday-Friday: Just query
python test_interactive_search.py --skip-upload
```

## Troubleshooting

**Database connection error?**
```bash
cd database
docker-compose up -d
cd ..
```

**Native PostgreSQL conflict?**
```bash
netstat -ano | findstr ":5432"
# If you see multiple processes, stop native PostgreSQL:
cd database
stop_native_postgres.bat
```

**Want to start over?**
```bash
python scripts/manage_database.py --clear
```

## What to Test

1. **Query variations** - Same question, different phrasings
2. **Cross-document search** - Questions spanning multiple PDFs
3. **Specific details** - Names, dates, numbers
4. **Chunk quality** - Use `chunk` command to inspect

## Performance Notes

- **Upload**: ~1 second per PDF (extraction + embedding)
- **Search**: < 1 second (even with 490 documents)
- **Database size**: ~1MB per 5-10 documents

## Ready to Go!

```bash
python test_interactive_search.py --skip-upload
```

Happy searching! 🔍
