$ErrorActionPreference = 'Stop'
# PDH GPU Engine counters; the parent retains only PIDs in the benchmark process tree.
Get-Counter '\GPU Engine(*)\Utilization Percentage' -Continuous -SampleInterval 1 | ForEach-Object {
    $values = @($_.CounterSamples | Where-Object { $_.CookedValue -gt 0 } | ForEach-Object {
        if ($_.InstanceName -match 'pid_(\d+)_.*engtype_(.*)') {
            @{pid=[int]$Matches[1]; engine=$Matches[2]; percent=$_.CookedValue}
        }
    })
    @{gpu=$values} | ConvertTo-Json -Compress -Depth 4
}
