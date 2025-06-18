$ids = Select-String "I didn't find a database entry for 'P" ".\$($args[0]).blg" | ForEach-Object {
  $_.line -replace ".*'P(\d+)'.*",'$1'
}

foreach ($id in $ids) {
  $related_entries = @()
  Write-Output "@artwork{P$id,eprint={P$id},eprinttype={cdli},"
  $json=(ConvertFrom-Json (Invoke-Webrequest "https://cdli.mpiwg-berlin.mpg.de/artifacts/$id/json").content);
  if ($json.museum_no.contains('—')) {
    Write-Output "number={$($json.excavation_no)},type={Excavation},"
  } else {
    Write-Output "number={$($json.museum_no)},"
  }
  foreach ($project in @('dcclt', 'epsd2', 'etcsri', 'dccmt')) {
    if (-not (invoke-webrequest "oracc.org/$project/P$id").content.contains('This project does not have the requested item')) {
      $related_entries+=("@artwork{P$id/oracc/$project, eprint={$project/P$id}, eprinttype={oracc}}")
      Write-Output "related={P$id/oracc/$project},"
    }
  }
  Write-Output "}"
  Write-Output "$related_entries"
}
