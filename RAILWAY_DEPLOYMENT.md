# 🚀 Railway Deployment Guide for TCC Assistant

## Prerequisites
- Railway account (free tier available)
- GitHub repository with your code
- MongoDB Atlas account (optional)

## Step 1: Prepare Your Repository

### Required Files (Already Created)
- ✅ `Procfile` - Railway startup command
- ✅ `railway.json` - Railway configuration
- ✅ `railway_startup.py` - Startup script
- ✅ `create_fallback_model.py` - Fallback model creator
- ✅ `railway.env.template` - Environment variables template

### Environment Variables Setup
Copy `railway.env.template` and set these in Railway dashboard:

```bash
# Required
PORT=5000
SECRET_KEY=your-secret-key-change-this-in-production

# Optional (for full functionality)
MONGODB_URI=mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/
PINECONE_API_KEY=pcsk_3LGtPm_F7RyLr4yFTu4C7bbEonvRcCxysxCztU9ADjyRefakqjq7wxqjJXVwt5JD5TeM62
```

## Step 2: Deploy to Railway

1. **Connect Repository**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Environment Variables**
   - Go to your project settings
   - Add environment variables from `railway.env.template`
   - At minimum, set `SECRET_KEY`

3. **Deploy**
   - Railway will automatically detect the `Procfile`
   - The deployment will run `railway_startup.py` first
   - Then start the Flask app with Gunicorn

## Step 3: Verify Deployment

### Check Logs
```bash
# In Railway dashboard, check the logs for:
✅ Railway startup checks completed
✅ MongoDB connected successfully (if URI provided)
✅ Neural network and vector store loaded successfully
🚀 Starting Flask application...
```

### Test Endpoints
- Main app: `https://your-app.railway.app`
- Predict endpoint: `https://your-app.railway.app/predict`

## Step 4: Troubleshooting

### Common Issues

1. **500 Error on /predict**
   - Check logs for import errors
   - Verify all packages in `requirements.txt`
   - Ensure `data.pth` model file exists

2. **MongoDB Connection Issues**
   - Verify `MONGODB_URI` is correct
   - Check MongoDB Atlas network access
   - App will work with fallback mode

3. **Model Loading Errors**
   - Run `python create_fallback_model.py` locally
   - Commit `data.pth` to repository
   - Or use fallback mode (already implemented)

4. **Memory Issues**
   - Railway free tier has memory limits
   - Consider upgrading for production use
   - Fallback mode uses less memory

### Debug Commands
```bash
# Check if model file exists
ls -la data.pth

# Test model loading
python -c "import torch; print(torch.load('data.pth'))"

# Test imports
python -c "from chat import get_response; print('OK')"
```

## Step 5: Production Optimization

### For Production Use
1. **Upgrade Railway Plan** - More memory and CPU
2. **Set Strong SECRET_KEY** - Generate random key
3. **Enable MongoDB** - For conversation logging
4. **Enable Pinecone** - For vector search
5. **Configure Email** - For notifications

### Performance Tips
- Use Railway's caching features
- Optimize model size
- Implement request rate limiting
- Monitor memory usage

## Step 6: Monitoring

### Railway Dashboard
- Monitor CPU and memory usage
- Check deployment logs
- Set up alerts for errors

### Application Monitoring
- Check `/predict` endpoint health
- Monitor response times
- Track error rates

## Support

If you encounter issues:
1. Check Railway logs first
2. Verify environment variables
3. Test locally with same configuration
4. Check Railway status page

## Features Available

### With Full Setup
- ✅ Neural network responses
- ✅ Vector search
- ✅ MongoDB conversation logging
- ✅ Multi-language support
- ✅ Office detection
- ✅ Admin portal

### With Fallback Mode
- ✅ Basic keyword responses
- ✅ Office-specific guidance
- ✅ Error handling
- ✅ Admin portal (limited)

---

**Note**: The app is designed to work even with missing dependencies, using fallback modes for graceful degradation.
