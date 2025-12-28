# Legal Search Pro - Production Deployment Guide

## 🚀 Quick Deploy to Railway

### Step 1: Prepare Your Repository
```bash
git init
git add .
git commit -m "Initial commit - Legal Search DBMS"
```

### Step 2: Create GitHub Repository
1. Go to https://github.com/new
2. Create new repository: `legal-case-dbms`
3. Push code:
```bash
git remote add origin https://github.com/YOUR_USERNAME/legal-case-dbms.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Railway
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `legal-case-dbms` repository
5. Railway will auto-detect Python and deploy!

### Step 4: Add PostgreSQL Database
1. In Railway project → Click "New" → "Database" → "PostgreSQL"
2. Railway automatically sets DATABASE_URL environment variable
3. Update your environment variables:
   - Click on your web service
   - Go to "Variables" tab
   - Add these variables:
     ```
     SECRET_KEY=your-random-secret-key-here
     FLASK_ENV=production
     GOOGLE_CLIENT_ID=your-google-client-id
     GOOGLE_CLIENT_SECRET=your-google-client-secret
     ```

### Step 5: Import Database Data
1. Get Railway PostgreSQL connection string from Variables tab
2. Use pgAdmin or psql to connect and import your data:
```bash
psql "postgresql://username:password@host:port/database" < backup.sql
```

### Step 6: Get Your Live URL
- Railway provides URL like: `https://legal-search-pro.railway.app`
- Update OAuth redirect URI in Google Console with new domain
- Update frontend API URLs to use production domain

---

## 🌐 Alternative: Deploy to Render

1. Go to https://render.com
2. New → Web Service → Connect GitHub repo
3. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn api:app`
4. Add PostgreSQL database from Render dashboard
5. Set environment variables same as Railway

---

## 📋 Environment Variables Needed

```env
# Database (auto-set by Railway/Render)
DATABASE_URL=postgresql://...

# Application
SECRET_KEY=generate-random-32-char-string
FLASK_ENV=production

# OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## ✅ Deployment Checklist

- [x] requirements.txt updated with all dependencies
- [x] Procfile created for gunicorn
- [x] runtime.txt specifies Python version
- [x] api.py uses environment variables
- [x] .gitignore excludes sensitive files
- [ ] Push code to GitHub
- [ ] Deploy on Railway/Render
- [ ] Add PostgreSQL database
- [ ] Import case data with embeddings
- [ ] Set environment variables
- [ ] Test live URL
- [ ] Update OAuth redirect URIs
- [ ] Add live URL to resume!

---

## 🎯 Resume-Ready Features

✅ **AI-Powered Search** - Semantic search using sentence transformers
✅ **Vector Similarity** - Real AI for finding related precedents
✅ **NLP Extraction** - Automated fact/citation extraction
✅ **Modern UI** - Responsive design with dark theme
✅ **PostgreSQL** - Production database with 2,160+ cases
✅ **RESTful API** - Clean API architecture
✅ **Cloud Deployed** - Live URL for demonstrations

---

## 📞 Troubleshooting

**Issue: Embeddings not importing**
- Solution: Use sentence-transformers to regenerate embeddings on production server

**Issue: Out of memory**
- Solution: Reduce embedding batch size or upgrade to Railway Pro plan

**Issue: Slow searches**
- Solution: Add database indexes on frequently queried columns

---

## 🔗 Important URLs After Deployment

- Live App: `https://your-app.railway.app`
- API Docs: `https://your-app.railway.app/api/stats`
- GitHub Repo: `https://github.com/your-username/legal-case-dbms`

Add all these to your resume! 🎉
