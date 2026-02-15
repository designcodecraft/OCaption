$rb = (New-Object -ComObject Shell.Application).Namespace(10)
foreach($item in $rb.Items()) {
    if ($item.Name -like "*1.6*" -or $item.Name -like "*latest*" -or $item.Name -like "*new*") {
        Write-Output "Name: $($item.Name)"
        Write-Output "Path: $($item.Path)"
        Write-Output "---"
    }
}
