# Quick Start Guide

## 🚀 First Time Setup

1. **Check if .NET is installed:**
   ```bash
   dotnet --version
   # Should show: 10.0.101 or higher
   ```

2. **Build the project:**
   ```bash
   dotnet build
   ```

3. **Run without SigNoz (local only):**
   ```bash
   dotnet run
   ```
   You'll see a warning about missing configuration, but it will work fine.

## 🔐 Setting Up SigNoz

### Method 1: Temporary (Current Session Only)
```bash
export SIGNOZ_REGION='in'  # or 'us', 'eu', etc.
export SIGNOZ_INGESTION_KEY='your-actual-key-here'
dotnet run
```

### Method 2: One-Time Run
```bash
SIGNOZ_REGION='in' SIGNOZ_INGESTION_KEY='your-actual-key-here' dotnet run
```

### Method 3: Permanent (Recommended)
Add to your shell config file (`~/.zshrc` for zsh or `~/.bashrc` for bash):
```bash
echo "export SIGNOZ_REGION='in'" >> ~/.zshrc
echo "export SIGNOZ_INGESTION_KEY='your-actual-key-here'" >> ~/.zshrc
source ~/.zshrc
```

## 📊 What You'll See

### With SigNoz Configuration Set:
- ✅ Logs in console (Serilog)
- ✅ Traces in console (OpenTelemetry)
- ✅ Traces sent to SigNoz cloud
- ✅ "OTLP exporter configured for SigNoz region: in" message

### Without SigNoz Configuration:
- ✅ Logs in console (Serilog)
- ✅ Traces in console (OpenTelemetry)
- ⚠️ Warning: "Missing SigNoz configuration: SIGNOZ_REGION, SIGNOZ_INGESTION_KEY"
- ❌ No traces sent to SigNoz

## 🔍 Verify It's Working

1. **Run the app:**
   ```bash
   SIGNOZ_REGION='in' SIGNOZ_INGESTION_KEY='your-key' dotnet run
   ```

2. **Check for success message:**
   Look for: `[INF] OTLP exporter configured for SigNoz region: in`

3. **View in SigNoz:**
   - Go to https://signoz.io
   - Navigate to Services → `serilog-otel-demo`
   - You should see traces appearing!

## 🛠️ Troubleshooting

**Problem:** "Missing SigNoz configuration: SIGNOZ_REGION, SIGNOZ_INGESTION_KEY"
- **Solution:** Export both variables before running (see methods above)

**Problem:** Traces not appearing in SigNoz
- **Check:** Are both region and key set correctly?
- **Check:** Is the region correct? (in, us, eu, etc.)
- **Check:** Is the endpoint reachable? (`https://ingest.{region}.signoz.cloud:443`)
- **Check:** Look for any error messages in the console output

**Problem:** Build errors
- **Solution:** Run `dotnet restore` then `dotnet build`

## 🎯 Next Steps

Once you have this working, you can:
1. Add more spans to trace different operations
2. Add custom attributes to your spans
3. Integrate HTTP instrumentation
4. Add database tracing
5. Correlate logs with traces
