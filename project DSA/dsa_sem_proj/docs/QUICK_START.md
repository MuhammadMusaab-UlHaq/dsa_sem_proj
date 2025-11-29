# QUICK START - NUST Navigation System

## 🚀 Ready in 3 Commands

```powershell
# 1. Clean old data
.\scripts\cleanup_data.ps1

# 2. Download and process map data (takes 2-3 minutes)
python data_pipeline.py

# 3. Launch the application
python main.py
```

---

## 🎯 For the Demo

### Test Route
1. **Start:** Type `Concordia` → Select `Concordia 1`
2. **End:** Type `Gate` → Select `NUST Gate 2`
3. **Mode:** Choose `2` (Driving)
4. **Result:** Blue route on map + time estimate

### Prove Smart Snapping
- Search for `Gate 2` as starting point
- Path will start **inside campus**, not on the highway
- This proves topology-aware snapping works!

---

## 📋 Pre-Demo Checklist

- [ ] Internet connected (for OSM data download)
- [ ] Virtual environment activated (`.\venv\Scripts\Activate.ps1`)
- [ ] Data files generated (run `python data_pipeline.py`)
- [ ] Test run completed successfully

---

## 🆘 Emergency Reset

```powershell
# If anything breaks, start fresh:
.\scripts\cleanup_data.ps1
python data_pipeline.py
python main.py
```

---

## 📞 Quick Help

**Problem:** No POIs loaded  
**Fix:** `python data_pipeline.py`

**Problem:** No path found  
**Fix:** Choose locations within NUST campus

**Problem:** Pipeline timeout  
**Fix:** Wait and retry (auto-switches servers)

---

**Ready? Run:** `python data_pipeline.py` then `python main.py`
