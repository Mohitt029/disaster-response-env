Write-Host "="*80 -ForegroundColor Green
Write-Host "🌊 TESTING DIFFERENT DISASTER TYPES" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

# ============================================================================
# Helper function to test a disaster type
# ============================================================================
function Test-DisasterType {
    param(
        [string]$DisasterName,
        [string]$Difficulty,
        [int]$ExpectedVictims,
        [string]$DisasterTypeValue
    )
    
    Write-Host "`n" + "="*70 -ForegroundColor Cyan
    Write-Host "📋 TESTING: $DisasterName ($Difficulty difficulty)" -ForegroundColor Cyan
    Write-Host "="*70 -ForegroundColor Cyan
    
    # Reset with the disaster type (passed as difficulty parameter)
    # Note: Our environment uses difficulty to select scenario type
    $reset = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/reset?difficulty=$Difficulty"
    $sessionId = $reset.session_id
    
    Write-Host "   Session: $($sessionId.Substring(0,8))..." -ForegroundColor Gray
    Write-Host "   Scenario: $($reset.observation.scenario_name)" -ForegroundColor Yellow
    Write-Host "   Disaster Type: $($reset.observation.disaster_type)" -ForegroundColor Yellow
    Write-Host "   Total Victims: $($reset.observation.total_victims)" -ForegroundColor Cyan
    Write-Host "   Available Resources: $($reset.observation.available_resources.Count)" -ForegroundColor Cyan
    
    # Run simulation for up to 40 steps
    $maxSteps = 40
    for ($i = 1; $i -le $maxSteps; $i++) {
        $a = '{"allocations":[{"resource_id":"resource_ambulance_0","victim_id":"victim_0000","priority":8}],"strategic":null,"confidence":0.85}'
        $step = Invoke-RestMethod -Method POST "http://localhost:8000/step?session_id=$sessionId" -Body $a -ContentType "application/json" -ErrorAction SilentlyContinue
        
        if ($step.observation) {
            if ($i % 10 -eq 0) {
                Write-Host "      Step $i : Rescued = $($step.observation.rescued_victims), Pending = $($step.observation.pending_victims.Count)" -ForegroundColor Gray
            }
        }
        
        if ($step.observation.done) {
            Write-Host "      Episode completed at step $i" -ForegroundColor Green
            break
        }
    }
    
    # Get final results
    $grader = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/grader?session_id=$sessionId"
    
    Write-Host "`n   📊 RESULTS:" -ForegroundColor Green
    Write-Host "      Lives Saved: $($grader.lives_saved)/$($reset.observation.total_victims)" -ForegroundColor $(if ($grader.lives_saved -eq $reset.observation.total_victims) { "Green" } else { "Yellow" })
    Write-Host "      Final Score: $([math]::Round($grader.score, 3))" -ForegroundColor $(if ($grader.score -ge 0.8) { "Green" } else { "Yellow" })
    Write-Host "      Feedback: $($grader.feedback)" -ForegroundColor Cyan
    
    return @{
        Name = $DisasterName
        Victims = $reset.observation.total_victims
        Rescued = $grader.lives_saved
        Score = $grader.score
    }
}

# ============================================================================
# TEST 1: EARTHQUAKE (Currently mapped to Medium difficulty)
# ============================================================================
$earthquakeResult = Test-DisasterType -DisasterName "EARTHQUAKE" -Difficulty "medium" -ExpectedVictims 35 -DisasterTypeValue "earthquake"

# ============================================================================
# TEST 2: FLOOD (Currently mapped to Easy difficulty)
# ============================================================================
$floodResult = Test-DisasterType -DisasterName "FLOOD" -Difficulty "easy" -ExpectedVictims 15 -DisasterTypeValue "flood"

# ============================================================================
# TEST 3: HURRICANE (Currently mapped to Hard difficulty)
# ============================================================================
$hurricaneResult = Test-DisasterType -DisasterName "HURRICANE" -Difficulty "hard" -ExpectedVictims 75 -DisasterTypeValue "hurricane"

# ============================================================================
# TEST 4: TSUNAMI (Testing with hard difficulty - would need generator update)
# ============================================================================
Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "📋 NOTE: TSUNAMI Simulation" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "   Tsunami would require modifications to disaster_data.py" -ForegroundColor Yellow
Write-Host "   Current generator supports: EARTHQUAKE, FLOOD, HURRICANE, WILDFIRE, TSUNAMI" -ForegroundColor Yellow
Write-Host "   To test Tsunami, we would need to modify the scenario generation." -ForegroundColor Yellow

# ============================================================================
# TEST 5: WILDFIRE (Testing with medium difficulty)
# ============================================================================
Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "📋 TESTING: WILDFIRE (using medium configuration)" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

# For wildfire, we need to manually create using the generator's internal method
# This would require modifying disaster_data.py to add a wildfire scenario
Write-Host "   Wildfire would require adding a generate_wildfire_scenario() method" -ForegroundColor Yellow
Write-Host "   to disaster_data.py. Current generator supports it but not exposed." -ForegroundColor Yellow

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📊 DISASTER TYPE TEST SUMMARY" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

Write-Host "`n   Disaster Type    | Difficulty | Victims | Rescued | Score" -ForegroundColor Cyan
Write-Host "   " + "-"*55 -ForegroundColor Gray

Write-Host "   EARTHQUAKE       | Medium     | $($earthquakeResult.Victims)      | $($earthquakeResult.Rescued)      | $([math]::Round($earthquakeResult.Score, 3))" -ForegroundColor White
Write-Host "   FLOOD            | Easy       | $($floodResult.Victims)      | $($floodResult.Rescued)      | $([math]::Round($floodResult.Score, 3))" -ForegroundColor White
Write-Host "   HURRICANE        | Hard       | $($hurricaneResult.Victims)      | $($hurricaneResult.Rescued)      | $([math]::Round($hurricaneResult.Score, 3))" -ForegroundColor White

Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "📝 RECOMMENDATIONS FOR NEW DISASTER TYPES:" -ForegroundColor Yellow
Write-Host "   1. To add TSUNAMI: Add 'generate_tsunami_scenario()' to disaster_data.py" -ForegroundColor White
Write-Host "   2. To add WILDFIRE: Add 'generate_wildfire_scenario()' to disaster_data.py" -ForegroundColor White
Write-Host "   3. Then update 'get_all_tasks()' to include new difficulty levels" -ForegroundColor White
Write-Host "="*80 -ForegroundColor Green
