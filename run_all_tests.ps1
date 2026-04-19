Write-Host "="*80 -ForegroundColor Green
Write-Host "🌊 DISASTER RESPONSE ENVIRONMENT - COMPLETE TEST SUITE" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

# Check server health
Write-Host "`n📌 1. SERVER HEALTH CHECK" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "   ✅ Server is running (Version: $($health.version))" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Server not running! Start with: uvicorn server.app:app --reload" -ForegroundColor Red
    exit 1
}

# Get available tasks
Write-Host "`n📌 2. AVAILABLE TASKS" -ForegroundColor Cyan
$tasks = Invoke-RestMethod -Uri "http://localhost:8000/tasks"
Write-Host "   ✅ Found $($tasks.tasks.Count) tasks:" -ForegroundColor Green
foreach ($task in $tasks.tasks) {
    Write-Host "      - $($task.id): $($task.description.Substring(0, [Math]::Min(50, $task.description.Length)))..." -ForegroundColor White
}

# ============================================================================
# TEST 1: EASY TASK (15 victims, 24 hours)
# ============================================================================
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📋 TEST 1: EASY TASK (15 victims, 24 hours)" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

$s = (Invoke-RestMethod -Method POST "http://localhost:8000/reset?difficulty=easy").session_id
Write-Host "Session: $($s.Substring(0,8))..." -ForegroundColor Gray

$easyResults = @()
for ($i = 1; $i -le 30; $i++) {
    $a = '{"allocations":[{"resource_id":"resource_ambulance_0","victim_id":"victim_0000","priority":8}],"strategic":null,"confidence":0.85}'
    $step = Invoke-RestMethod -Method POST "http://localhost:8000/step?session_id=$s" -Body $a -ContentType "application/json" -ErrorAction SilentlyContinue
    if ($step.observation) {
        $easyResults += $step.observation.rescued_victims
        if ($i % 5 -eq 0) {
            Write-Host "   Step $i : Rescued = $($step.observation.rescued_victims), Pending = $($step.observation.pending_victims.Count)" -ForegroundColor Cyan
        }
    }
    if ($step.observation.done) { break }
}
$easyGrader = Invoke-RestMethod -Method POST "http://localhost:8000/grader?session_id=$s"
Write-Host "`n   ✅ EASY TASK RESULTS:" -ForegroundColor Green
Write-Host "      Lives Saved: $($easyGrader.lives_saved)/15" -ForegroundColor $(if ($easyGrader.lives_saved -eq 15) { "Green" } else { "Yellow" })
Write-Host "      Final Score: $([math]::Round($easyGrader.score, 3))" -ForegroundColor $(if ($easyGrader.score -ge 0.9) { "Green" } else { "Yellow" })
Write-Host "      Feedback: $($easyGrader.feedback)" -ForegroundColor Cyan

# ============================================================================
# TEST 2: MEDIUM TASK (35 victims, 48 hours)
# ============================================================================
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📋 TEST 2: MEDIUM TASK (35 victims, 48 hours)" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

$s = (Invoke-RestMethod -Method POST "http://localhost:8000/reset?difficulty=medium").session_id
Write-Host "Session: $($s.Substring(0,8))..." -ForegroundColor Gray

$mediumResults = @()
for ($i = 1; $i -le 50; $i++) {
    $a = '{"allocations":[{"resource_id":"resource_ambulance_0","victim_id":"victim_0000","priority":8}],"strategic":null,"confidence":0.85}'
    $step = Invoke-RestMethod -Method POST "http://localhost:8000/step?session_id=$s" -Body $a -ContentType "application/json" -ErrorAction SilentlyContinue
    if ($step.observation) {
        $mediumResults += $step.observation.rescued_victims
        if ($i % 10 -eq 0) {
            Write-Host "   Step $i : Rescued = $($step.observation.rescued_victims), Pending = $($step.observation.pending_victims.Count)" -ForegroundColor Cyan
        }
    }
    if ($step.observation.done) { break }
}
$mediumGrader = Invoke-RestMethod -Method POST "http://localhost:8000/grader?session_id=$s"
Write-Host "`n   ✅ MEDIUM TASK RESULTS:" -ForegroundColor Green
Write-Host "      Lives Saved: $($mediumGrader.lives_saved)/35" -ForegroundColor $(if ($mediumGrader.lives_saved -ge 33) { "Green" } else { "Yellow" })
Write-Host "      Final Score: $([math]::Round($mediumGrader.score, 3))" -ForegroundColor $(if ($mediumGrader.score -ge 0.85) { "Green" } else { "Yellow" })
Write-Host "      Feedback: $($mediumGrader.feedback)" -ForegroundColor Cyan

# ============================================================================
# TEST 3: HARD TASK (75 victims, 72 hours)
# ============================================================================
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📋 TEST 3: HARD TASK (75 victims, 72 hours)" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

$s = (Invoke-RestMethod -Method POST "http://localhost:8000/reset?difficulty=hard").session_id
Write-Host "Session: $($s.Substring(0,8))..." -ForegroundColor Gray

$hardResults = @()
for ($i = 1; $i -le 80; $i++) {
    $a = '{"allocations":[{"resource_id":"resource_ambulance_0","victim_id":"victim_0000","priority":8}],"strategic":null,"confidence":0.85}'
    $step = Invoke-RestMethod -Method POST "http://localhost:8000/step?session_id=$s" -Body $a -ContentType "application/json" -ErrorAction SilentlyContinue
    if ($step.observation) {
        $hardResults += $step.observation.rescued_victims
        if ($i % 15 -eq 0) {
            Write-Host "   Step $i : Rescued = $($step.observation.rescued_victims), Pending = $($step.observation.pending_victims.Count)" -ForegroundColor Cyan
        }
    }
    if ($step.observation.done) { break }
}
$hardGrader = Invoke-RestMethod -Method POST "http://localhost:8000/grader?session_id=$s"
Write-Host "`n   ✅ HARD TASK RESULTS:" -ForegroundColor Green
Write-Host "      Lives Saved: $($hardGrader.lives_saved)/75" -ForegroundColor $(if ($hardGrader.lives_saved -ge 65) { "Green" } elseif ($hardGrader.lives_saved -ge 50) { "Yellow" } else { "Red" })
Write-Host "      Final Score: $([math]::Round($hardGrader.score, 3))" -ForegroundColor $(if ($hardGrader.score -ge 0.8) { "Green" } else { "Yellow" })
Write-Host "      Feedback: $($hardGrader.feedback)" -ForegroundColor Cyan

# ============================================================================
# TEST 4: METRICS DASHBOARD
# ============================================================================
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📋 TEST 4: METRICS DASHBOARD" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

$metrics = Invoke-RestMethod -Uri "http://localhost:8000/metrics"
Write-Host "   Total Episodes: $($metrics.total_episodes)" -ForegroundColor Green
Write-Host "   Average Scores:" -ForegroundColor Yellow
foreach ($diff in $metrics.average_scores.PSObject.Properties) {
    Write-Host "      - $($diff.Name): $([math]::Round($diff.Value, 3))" -ForegroundColor White
}
Write-Host "   Total Lives Saved:" -ForegroundColor Yellow
foreach ($diff in $metrics.total_lives_saved.PSObject.Properties) {
    Write-Host "      - $($diff.Name): $($diff.Value)" -ForegroundColor White
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📊 TEST SUMMARY" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

Write-Host "`n   Easy Task:   $($easyGrader.lives_saved)/15 rescued (Score: $([math]::Round($easyGrader.score, 3)))" -ForegroundColor $(if ($easyGrader.lives_saved -eq 15) { "Green" } else { "Yellow" })
Write-Host "   Medium Task: $($mediumGrader.lives_saved)/35 rescued (Score: $([math]::Round($mediumGrader.score, 3)))" -ForegroundColor $(if ($mediumGrader.lives_saved -ge 33) { "Green" } else { "Yellow" })
Write-Host "   Hard Task:   $($hardGrader.lives_saved)/75 rescued (Score: $([math]::Round($hardGrader.score, 3)))" -ForegroundColor $(if ($hardGrader.lives_saved -ge 65) { "Green" } else { "Yellow" })

$avgScore = ($easyGrader.score + $mediumGrader.score + $hardGrader.score) / 3
Write-Host "`n   OVERALL AVERAGE SCORE: $([math]::Round($avgScore, 3))" -ForegroundColor Cyan

Write-Host "`n" + "="*80 -ForegroundColor Green
if ($easyGrader.lives_saved -eq 15 -and $mediumGrader.lives_saved -ge 30 -and $hardGrader.lives_saved -ge 60) {
    Write-Host "🎉 EXCELLENT! All tests passed! Environment is production-ready!" -ForegroundColor Green
} elseif ($easyGrader.lives_saved -eq 15 -and $mediumGrader.lives_saved -ge 25) {
    Write-Host "✅ GOOD! Most tests passed. Consider optimizing hard task strategy." -ForegroundColor Yellow
} else {
    Write-Host "⚠️ Some tests need improvement. Review resource allocation strategy." -ForegroundColor Yellow
}
Write-Host "="*80 -ForegroundColor Green
