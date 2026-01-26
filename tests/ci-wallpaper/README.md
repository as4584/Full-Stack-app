# 🖼️ Wallpaper Asset Reliability CI System

**Mission:** Ensure wallpaper.gif assets never break or silently disappear on production pages.

## 🎯 Target Pages

- **Home Page:** https://lexmakesit.com
- **AI Receptionist:** https://lexmakesit.com/projects/ai-receptionist

## 🔄 Triggers

- ✅ Every Pull Request
- ✅ Every Deploy to main/develop
- ✅ Nightly automated checks (2 AM UTC)
- ✅ Manual workflow dispatch

## 📋 Test Phases

### Phase 1: Asset Availability
**Goal:** Verify wallpaper.gif files exist and are valid

**Checks:**
- HTTP GET requests to wallpaper URLs
- Status code 200 verification
- Content-Type = image/gif validation
- File size > minimum threshold
- GIF format validation (magic bytes)

**Failure Conditions:**
- 404, 403, or 500 responses
- Wrong MIME type
- Empty or corrupted files

### Phase 2: Rendering Validation
**Goal:** Verify wallpapers render and animate on pages

**Checks:**
- Load target pages with Playwright
- Locate wallpaper elements
- Verify background-image CSS applied
- Detect GIF animation (frame changes)
- Capture screenshots for verification

**Failure Conditions:**
- Background image missing
- Broken CSS references
- Static or unloaded GIFs

### Phase 3: Cache Safety
**Goal:** Verify cache headers and CDN behavior

**Checks:**
- Cache-Control header validation
- ETag/Last-Modified presence
- CDN header inspection
- Cache consistency testing
- Stale reference detection

**Failure Conditions:**
- Missing cache headers
- Inappropriate cache settings
- Inconsistent responses

### Phase 4: Visual Regression
**Goal:** Detect wallpaper changes and visual regressions

**Checks:**
- Screenshot capture with wallpapers visible
- Animation frame analysis
- Baseline comparison
- Visual hash generation

**Failure Conditions:**
- Wallpaper disappears
- Unexpected visual changes
- Position/size modifications

## 🚀 Usage

### Run All Tests
```bash
cd tests/ci-wallpaper
./run_wallpaper_tests.sh all
```

### Run Individual Phases
```bash
./run_wallpaper_tests.sh phase1  # Asset availability
./run_wallpaper_tests.sh phase2  # Rendering validation
./run_wallpaper_tests.sh phase3  # Cache safety
./run_wallpaper_tests.sh phase4  # Visual regression
```

### Create Visual Baseline
```bash
./run_wallpaper_tests.sh phase4 --create-baseline
```

### Verbose Output
```bash
./run_wallpaper_tests.sh all --verbose
```

### Continue on Errors
```bash
./run_wallpaper_tests.sh all --continue-on-error
```

## 📁 Directory Structure

```
tests/ci-wallpaper/
├── README.md                          # This documentation
├── run_wallpaper_tests.sh             # Main test runner
├── requirements.txt                   # Python dependencies
├── wallpaper_config.json              # Configuration file
├── phase1_asset_availability.py       # HTTP validation
├── phase2_rendering_validation.py     # Browser testing
├── phase3_cache_safety.py             # Cache validation
├── phase4_visual_regression.py        # Visual comparison
└── snapshots/                         # Screenshots and baselines
    ├── visual_baseline.json           # Visual regression baseline
    ├── wallpaper_*.png                # Page screenshots
    └── visual_comparison_*.json       # Comparison reports
```

## 🔧 Dependencies

- **Python 3.11+**
- **aiohttp:** Async HTTP requests
- **playwright:** Browser automation
- **Pillow:** Image processing
- **requests:** HTTP client

## 🎮 GitHub Actions Integration

The system runs automatically via GitHub Actions:

**Workflow:** `.github/workflows/wallpaper-ci.yml`

**Matrix Strategy:** Parallel execution of all phases

**Artifacts:**
- Screenshots (30-day retention)
- Test reports (7-day retention)
- Comparison data

**PR Comments:** Automatic summary with pass/fail status

## 📊 Interpreting Results

### ✅ Success Indicators
```
🎉 ALL WALLPAPER TESTS PASSED - Assets are safe for deployment!
  ✅ Wallpaper assets are accessible and valid
  ✅ Wallpapers render correctly on all target pages
  ✅ Cache configuration is optimized and safe
  ✅ No visual regressions detected
```

### ❌ Failure Indicators
```
🚨 WALLPAPER TESTS FAILED - DO NOT DEPLOY
  ❌ Wallpaper assets may be broken or missing
  ❌ Users may see broken backgrounds or empty pages
  ❌ Brand consistency is at risk
```

## 🛠️ Troubleshooting

### Phase 1 Failures
- **404 Errors:** Check if wallpaper files exist at expected URLs
- **Wrong MIME:** Ensure files are actually GIF format
- **Size Issues:** Verify files aren't corrupted or empty

### Phase 2 Failures
- **Rendering Issues:** Check CSS background-image properties
- **Animation Problems:** Verify GIF has multiple frames
- **Element Not Found:** Update CSS selectors in configuration

### Phase 3 Failures
- **Cache Headers:** Configure appropriate Cache-Control headers
- **CDN Issues:** Check CDN configuration and cache behavior
- **Consistency:** Investigate server-side caching problems

### Phase 4 Failures
- **Visual Changes:** Review screenshot differences
- **Baseline Issues:** Consider creating new baseline if intentional
- **Position Changes:** Check CSS layout modifications

## 📈 Configuration

Edit `wallpaper_config.json` to:
- Add new target pages
- Modify wallpaper selectors
- Adjust validation thresholds
- Configure cache requirements

## 🔄 Maintenance

### Update Baselines
When wallpapers are intentionally changed:
```bash
./run_wallpaper_tests.sh phase4 --create-baseline
```

### Add New Pages
1. Update `wallpaper_config.json`
2. Test locally: `./run_wallpaper_tests.sh all`
3. Create new baseline if needed

### Monitor Nightly Runs
Check GitHub Actions for automated nightly results to catch issues early.

## 🚨 Emergency Procedures

### Production Wallpaper Broken
1. **Immediate:** Revert to last known good commit
2. **Investigation:** Run `./run_wallpaper_tests.sh all --verbose`
3. **Fix:** Address specific phase failures
4. **Verify:** Re-run tests before deploying fix

### False Positives
1. Check if wallpaper URLs changed
2. Verify CDN configuration
3. Update configuration if needed
4. Re-run tests to confirm

---

**Remember:** Visual regressions block deployment. This system protects brand consistency and user experience.