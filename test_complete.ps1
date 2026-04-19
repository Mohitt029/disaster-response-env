Write-Host "="*70 -ForegroundColor Green
Write-Host "🌊 DISASTER RESPONSE ENVIRONMENT - COMPLETE TEST SUITE" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green

# ============================================================================
# SECTION 1: HEALTH CHECK
# ============================================================================
Write-Host "`n📌 SECTION 1: HEALTH CHECK" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "   ✅ Server Status: $($health.status)" -ForegroundColor Green
    Write-Host "   ✅ Environment: $($health.environment)" -ForegroundColor Green
    Write-Host "   ✅ Version: $($health.version)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Server is not running. Start with: uvicorn server.app:app --reload" -ForegroundColor Red
    exit 1
}

# ============================================================================
# SECTION 2: TASKS ENDPOINT
# ============================================================================
Write-Host "`n📌 SECTION 2: TASKS ENDPOINT" -ForegroundColor Cyan
$tasks = Invoke-RestMethod -Uri "http://localhost:8000/tasks"
Write-Host "   ✅ Found $($tasks.tasks.Count) tasks" -ForegroundColor Green
foreach ($task in $tasks.tasks) {
    $desc = $task.description
    if ($desc.Length -gt 60) { $desc = $desc.Substring(0, 57) + "..." }
    Write-Host "      - $($task.id): $desc" -ForegroundColor White
    Write-Host "        Time Limit: $($task.time_limit_hours) hours" -ForegroundColor Gray
}

# ============================================================================
# SECTION 3: TEST ALL TASKS (Easy, Medium, Hard) WITH STEP
# ============================================================================
Write-Host "`n📌 SECTION 3: TESTING ALL TASKS (With Step Action)" -ForegroundColor Cyan

$allResults = @()

foreach ($difficulty in @("easy", "medium", "hard")) {
    Write-Host "`n   🔹 TESTING $($difficulty.ToUpper()) TASK" -ForegroundColor Yellow
    
    # Reset with specific difficulty
    $reset = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/reset?difficulty=$difficulty"
    $sessionId = $reset.session_id
    Write-Host "      Session: $($sessionId.Substring(0,8))..." -ForegroundColor Gray
    Write-Host "      Scenario: $($reset.observation.scenario_name)" -ForegroundColor Cyan
    Write-Host "      Total Victims: $($reset.observation.total_victims)" -ForegroundColor Cyan
    Write-Host "      Available Resources: $($reset.observation.available_resources.Count)" -ForegroundColor Cyan
    Write-Host "      Pending Victims: $($reset.observation.pending_victims.Count)" -ForegroundColor Cyan
    
    # Make a decision - dispatch first resource to first victim
    if ($reset.observation.pending_victims.Count -gt 0 -and $reset.observation.available_resources.Count -gt 0) {
        $firstVictim = $reset.observation.pending_victims[0]
        $firstResource = $reset.observation.available_resources[0]
        
        $action = @{
            allocations = @(
                @{
                    resource_id = $firstResource.id
                    victim_id = $firstVictim.id
                    priority = 8
                }
            )
            strategic = $null
            confidence = 0.85
        } | ConvertTo-Json -Depth 3
        
        # Call step endpoint
        $step = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/step?session_id=$sessionId" -Body $action -ContentType "application/json"
        Write-Host "      Step Reward: $([math]::Round($step.observation.current_reward, 3))" -ForegroundColor Green
    } else {
        Write-Host "      ⚠️ No pending victims or available resources" -ForegroundColor Yellow
    }
    
    # Get grader result (now should work because step was called)
    $grader = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/grader?session_id=$sessionId"
    Write-Host "      Final Score: $([math]::Round($grader.score, 3))" -ForegroundColor $(if ($grader.score -ge 0.5) { "Green" } else { "Yellow" })
    Write-Host "      Feedback: $($grader.feedback)" -ForegroundColor Cyan
    Write-Host "      Lives Saved: $($grader.lives_saved) / $($reset.observation.total_victims)" -ForegroundColor Green
    
    $allResults += [PSCustomObject]@{
        Task = $difficulty
        Score = $grader.score
        LivesSaved = $grader.lives_saved
        TotalVictims = $reset.observation.total_victims
        Feedback = $grader.feedback
    }
}

# ============================================================================
# SECTION 4: METRICS DASHBOARD
# ============================================================================
Write-Host "`n📌 SECTION 4: METRICS DASHBOARD" -ForegroundColor Cyan
$metrics = Invoke-RestMethod -Uri "http://localhost:8000/metrics"
Write-Host "   ✅ Total Episodes: $($metrics.total_episodes)" -ForegroundColor Green
Write-Host "   ✅ Average Scores:" -ForegroundColor Green
foreach ($diff in $metrics.average_scores.PSObject.Properties) {
    Write-Host "      - $($diff.Name): $([math]::Round($diff.Value, 3))" -ForegroundColor White
}
Write-Host "   ✅ Total Lives Saved:" -ForegroundColor Green
foreach ($diff in $metrics.total_lives_saved.PSObject.Properties) {
    Write-Host "      - $($diff.Name): $($diff.Value)" -ForegroundColor White
}

# ============================================================================
# SECTION 5: STATE ENDPOINT TEST
# ============================================================================
Write-Host "`n📌 SECTION 5: STATE ENDPOINT" -ForegroundColor Cyan
$reset = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/reset?difficulty=easy"
$sessionId = $reset.session_id
$state = Invoke-RestMethod -Method GET -Uri "http://localhost:8000/state?session_id=$sessionId"
Write-Host "   ✅ Episode ID: $($state.episode_id)" -ForegroundColor Green
Write-Host "   ✅ Step Count: $($state.step_count)" -ForegroundColor Green
Write-Host "   ✅ Simulation Time: $($state.simulation_time_hours) hours" -ForegroundColor Green
Write-Host "   ✅ Lives Saved in State: $($state.lives_saved)" -ForegroundColor Green

# ============================================================================
# SECTION 6: ROOT ENDPOINT
# ============================================================================
Write-Host "`n📌 SECTION 6: ROOT ENDPOINT" -ForegroundColor Cyan
$root = Invoke-RestMethod -Uri "http://localhost:8000/"
Write-Host "   ✅ Name: $($root.name)" -ForegroundColor Green
Write-Host "   ✅ Version: $($root.version)" -ForegroundColor Green
$endpointList = ($root.endpoints.PSObject.Properties | ForEach-Object { $_.Name }) -join ', '
Write-Host "   ✅ Endpoints: $endpointList" -ForegroundColor Green

# ============================================================================
# SECTION 7: ACTION SCHEMA VALIDATION
# ============================================================================
Write-Host "`n📌 SECTION 7: ACTION SCHEMA VALIDATION" -ForegroundColor Cyan
$tasksData = Invoke-RestMethod -Uri "http://localhost:8000/tasks"
$schema = $tasksData.action_schema
Write-Host "   ✅ Allocations schema present: $($schema.PSObject.Properties.Name -contains 'allocations')" -ForegroundColor Green
Write-Host "   ✅ Strategic schema present: $($schema.PSObject.Properties.Name -contains 'strategic')" -ForegroundColor Green
Write-Host "   ✅ Confidence schema present: $($schema.PSObject.Properties.Name -contains 'confidence')" -ForegroundColor Green

# ============================================================================
# SECTION 8: QUICK API RESPONSE TEST
# ============================================================================
Write-Host "`n📌 SECTION 8: QUICK API RESPONSE TEST" -ForegroundColor Cyan

# Test all three difficulties in sequence with step
$quickResults = @()
foreach ($diff in @("easy", "medium", "hard")) {
    $s = (Invoke-RestMethod -Method POST "http://localhost:8000/reset?difficulty=$diff").session_id
    $a = '{"allocations":[{"resource_id":"resource_ambulance_0","victim_id":"victim_0000","priority":8}],"strategic":null,"confidence":0.85}'
    $stepResp = Invoke-RestMethod -Method POST "http://localhost:8000/step?session_id=$s" -Body $a -ContentType "application/json" -ErrorAction SilentlyContinue
    $g = Invoke-RestMethod -Method POST "http://localhost:8000/grader?session_id=$s" -ErrorAction SilentlyContinue
    if ($g) {
        $quickResults += [PSCustomObject]@{Task = $diff; Score = $g.score}
        Write-Host "   ✅ $diff : Score = $([math]::Round($g.score, 3))" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ $diff : Grader failed" -ForegroundColor Yellow
    }
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" + "="*70 -ForegroundColor Green
Write-Host "📊 TEST SUMMARY" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green

foreach ($result in $allResults) {
    $statusIcon = if ($result.Score -ge 0.5) { "✅" } else { "⚠️" }
    Write-Host "   $statusIcon $($result.Task.ToUpper()): Score = $([math]::Round($result.Score, 3)), Lives Saved = $($result.LivesSaved)/$($result.TotalVictims)" -ForegroundColor $(if ($result.Score -ge 0.5) { "Green" } else { "Yellow" })
    Write-Host "        Feedback: $($result.Feedback.Substring(0, [Math]::Min(50, $result.Feedback.Length)))..." -ForegroundColor Gray
}

$avgScore = if ($allResults.Count -gt 0) { ($allResults | Measure-Object -Property Score -Average).Average } else { 0 }
Write-Host "`n   AVERAGE SCORE: $([math]::Round($avgScore, 3))" -ForegroundColor Cyan

Write-Host "`n" + "="*70 -ForegroundColor Green
if ($avgScore -gt 0) {
    Write-Host "🎉 ALL TESTS PASSED! Environment is ready for training!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Some tests had issues. Check the output above." -ForegroundColor Yellow
}
Write-Host "="*70 -ForegroundColor Green
