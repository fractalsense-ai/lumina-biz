[CmdletBinding()]
param([ValidateRange(1, 65535)][int]$Port = 18081)

$ErrorActionPreference = "Stop"
$baseUrl = "http://127.0.0.1:$Port"
$frontend = "lumina-lumen-eval-frontend-1"
$project = & docker inspect --format '{{ index .Config.Labels "com.docker.compose.project" }}' $frontend
if ($LASTEXITCODE -ne 0 -or $project.Trim() -ne "lumina-lumen-eval") { throw "The isolated evaluation frontend is not running." }
$binding = & docker port $frontend 8080/tcp
if ($LASTEXITCODE -ne 0 -or $binding -ne "127.0.0.1:$Port") { throw "The selected port is not bound to the isolated evaluation frontend." }
$secretFile = Join-Path $env:TEMP "lumina-lumen-evaluation-secrets.json"
if (-not (Test-Path $secretFile)) { throw "Evaluation credentials are missing." }
$credentials = Get-Content -Raw $secretFile | ConvertFrom-Json
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$login = @{ usr = "Administrator"; pwd = $credentials.administrator } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/method/login" -Method Post -ContentType "application/json" -Body $login -WebSession $session | Out-Null
$page = Invoke-WebRequest -Uri "$baseUrl/pos" -WebSession $session
$match = [regex]::Match($page.Content, 'window\.csrf_token\s*=\s*"([^"]+)"')
if (-not $match.Success) { throw "POS page did not expose a CSRF token." }
$headers = @{ "X-Frappe-CSRF-Token" = $match.Groups[1].Value }

function Invoke-EvaluationMethod([string]$Method, [hashtable]$Payload) {
    $json = $Payload | ConvertTo-Json -Depth 20 -Compress
    $response = Invoke-RestMethod -Uri "$baseUrl/api/method/$Method" -Method Post -ContentType "application/json" -Body $json -WebSession $session -Headers $headers
    return $response.message
}

$profile = "Lumen Riyadh Olaya"
$profilePath = [Uri]::EscapeDataString($profile)
$profileBody = @{ lumenpos_restaurant_mode = 1; lumenpos_kitchen_printer_ip = ""; lumenpos_printer_ip = "" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/resource/POS%20Profile/$profilePath" -Method Put -ContentType "application/json" -Body $profileBody -WebSession $session -Headers $headers | Out-Null

$tableNumber = "EVAL-" + [Guid]::NewGuid().ToString("N").Substring(0, 8)
$table = Invoke-EvaluationMethod "lumen_restaurants.api.restaurant.save_table" @{ pos_profile = $profile; table_no = $tableNumber; seats = 2 }
$order = Invoke-EvaluationMethod "lumen_restaurants.api.restaurant.open_order" @{ pos_profile = $profile; table = $table.name; order_type = "Dine in"; guests = 2 }
$cart = @{ lines = @(@{ item_code = "BEV-003"; item_name = "Orange Juice 1L"; qty = 1; price = 9; note = "Evaluation only" }) }
Invoke-EvaluationMethod "lumen_restaurants.api.restaurant.save_order" @{ name = $order.name; cart = $cart } | Out-Null
$ticket = Invoke-EvaluationMethod "lumen_restaurants.api.kitchen.send_to_kitchen" @{ order = $order.name; items = @(@{ item_code = "BEV-003"; item_name = "Orange Juice 1L"; qty = 1; note = "Evaluation only" }) }
if (-not $ticket.ticket) { throw "Kitchen ticket was not created." }

$sale = @{ pos_profile = $profile; items = @(@{ item_code = "BEV-003"; qty = 1 }); order = $order.name; idempotency_key = [Guid]::NewGuid().ToString("N") }
$quote = Invoke-EvaluationMethod "lumen_restaurants.api.sales.quote_sale" @{ payload = $sale }
if ($quote.payable -le 0) { throw "Synthetic order did not produce a positive quote." }
$sale.payments = @(@{ mode_of_payment = "Cash"; amount = $quote.payable })
$receipt = Invoke-EvaluationMethod "lumen_restaurants.api.sales.submit_sale" @{ payload = $sale }
if (-not $receipt.name -or $receipt.doctype -ne "POS Invoice") { throw "Sale did not return a POS Invoice identifier." }

$invoicePath = [Uri]::EscapeDataString($receipt.name)
$invoice = (Invoke-RestMethod -Uri "$baseUrl/api/resource/POS%20Invoice/$invoicePath" -WebSession $session).data
$orderPath = [Uri]::EscapeDataString($order.name)
$savedOrder = (Invoke-RestMethod -Uri "$baseUrl/api/resource/POS%20Restaurant%20Order/$orderPath" -WebSession $session).data
if ($invoice.docstatus -ne 1 -or $invoice.status -ne "Paid") { throw "ERPNext invoice is not submitted and paid." }
if ($savedOrder.status -ne "Closed" -or $receipt.name -notin @($savedOrder.invoices.invoice)) { throw "The restaurant order did not close with the paid invoice linked." }

Write-Output "PASS: table order $($order.name), kitchen ticket $($ticket.ticket), paid POS Invoice $($receipt.name), order closed."