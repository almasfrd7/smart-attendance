<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function respond(int $status, array $body): never
{
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}

function fail(int $status, string $message): never
{
    respond($status, ['error' => $message]);
}

function readRecord(array $input): array
{
    $record = [];
    foreach (['User ID', 'Name', 'Date', 'Time', 'Status'] as $field) {
        if (!isset($input[$field]) || !is_string($input[$field])) {
            fail(400, "A valid {$field} is required.");
        }
        $record[$field] = trim($input[$field]);
        if ($record[$field] === '' || strlen($record[$field]) > 200 || preg_match('/[\x00-\x1F\x7F]/', $record[$field])) {
            fail(400, "A valid {$field} is required.");
        }
    }

    if (!preg_match('/^[1-9][0-9]{0,19}$/', $record['User ID'])) {
        fail(400, 'User ID must be a positive number without leading zeroes.');
    }

    $date = DateTimeImmutable::createFromFormat('!Y-m-d', $record['Date']);
    if (!$date || $date->format('Y-m-d') !== $record['Date']) {
        fail(400, 'Date must be a valid YYYY-MM-DD date.');
    }

    if (!preg_match('/^(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?$/', $record['Time'])) {
        fail(400, 'Time must be a valid 24-hour time.');
    }
    if (strlen($record['Time']) === 5) {
        $record['Time'] .= ':00';
    }

    return $record;
}

function writeCsv($file, array $headers, array $rows): void
{
    if (!rewind($file) || !ftruncate($file, 0)) {
        fail(500, 'Could not update the attendance CSV.');
    }

    if (fputcsv($file, $headers, ',', '"', '') === false) {
        fail(500, 'Could not write the attendance CSV header.');
    }

    foreach ($rows as $row) {
        $values = [];
        foreach ($headers as $header) {
            $values[] = $row[$header] ?? '';
        }
        if (fputcsv($file, $values, ',', '"', '') === false) {
            fail(500, 'Could not write an attendance record.');
        }
    }

    if (!fflush($file)) {
        fail(500, 'Could not save the attendance CSV.');
    }
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if (!in_array($method, ['GET', 'POST', 'PUT', 'DELETE'], true)) {
    header('Allow: GET, POST, PUT, DELETE');
    fail(405, 'Method not allowed.');
}

$input = [];
if ($method !== 'GET') {
    if (($_SERVER['HTTP_X_ATTENDANCE_REQUEST'] ?? '') !== '1') {
        fail(403, 'Request verification failed.');
    }
    if (stripos($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== 0) {
        fail(415, 'Requests must use JSON.');
    }

    $input = json_decode(file_get_contents('php://input'), true);
    if (!is_array($input)) {
        fail(400, 'Invalid JSON request.');
    }
}

$directory = __DIR__ . DIRECTORY_SEPARATOR . 'attendance';
if (!is_dir($directory) && !mkdir($directory, 0775, true) && !is_dir($directory)) {
    fail(500, 'Could not access the attendance folder.');
}

$path = $directory . DIRECTORY_SEPARATOR . 'attendance.csv';
$file = @fopen($path, 'c+');
if ($file === false) {
    fail(500, 'Could not open attendance/attendance.csv. Check folder permissions.');
}
if (!flock($file, LOCK_EX)) {
    fclose($file);
    fail(500, 'Could not lock the attendance CSV.');
}

try {
    rewind($file);
    $headers = fgetcsv($file, null, ',', '"', '');
    if ($headers === false) {
        $headers = ['User ID', 'Name', 'Date', 'Time', 'Status', 'Record ID'];
    } else {
        $headers[0] = preg_replace('/^\xEF\xBB\xBF/', '', (string) $headers[0]);
    }

    $requiredHeaders = ['User ID', 'Name', 'Date', 'Time', 'Status'];
    foreach ($requiredHeaders as $header) {
        if (!in_array($header, $headers, true)) {
            fail(422, "The attendance CSV is missing the {$header} column.");
        }
    }
    if (!in_array('Record ID', $headers, true)) {
        $headers[] = 'Record ID';
    }

    $rows = [];
    $ids = [];
    $changed = false;
    while (($values = fgetcsv($file, null, ',', '"', '')) !== false) {
        if ($values === [null]) {
            continue;
        }
        $row = [];
        foreach ($headers as $index => $header) {
            $row[$header] = (string) ($values[$index] ?? '');
        }

        $id = $row['Record ID'] ?? '';
        if (!preg_match('/^[a-f0-9]{32}$/', $id) || isset($ids[$id])) {
            do {
                $id = bin2hex(random_bytes(16));
            } while (isset($ids[$id]));
            $row['Record ID'] = $id;
            $changed = true;
        }
        $ids[$id] = true;
        $rows[] = $row;
    }

    if ($method === 'POST' || $method === 'PUT') {
        $record = readRecord($input['record'] ?? []);
        foreach ($rows as $index => $row) {
            if (
                $row['User ID'] === $record['User ID']
                && $row['Date'] === $record['Date']
                && ($method === 'POST' || $row['Record ID'] !== ($input['id'] ?? ''))
            ) {
                fail(409, 'This user already has an attendance record for that date.');
            }
        }

        if ($method === 'POST') {
            $record['Record ID'] = bin2hex(random_bytes(16));
            $rows[] = $record;
            $changed = true;
            $savedRecord = $record;
        } else {
            $id = $input['id'] ?? '';
            $index = null;
            foreach ($rows as $rowIndex => $row) {
                if ($row['Record ID'] === $id) {
                    $index = $rowIndex;
                    break;
                }
            }
            if ($index === null) {
                fail(404, 'Attendance record not found.');
            }
            $record['Record ID'] = $id;
            foreach ($requiredHeaders as $header) {
                $rows[$index][$header] = $record[$header];
            }
            $changed = true;
            $savedRecord = $rows[$index];
        }
    } elseif ($method === 'DELETE') {
        $id = $input['id'] ?? '';
        $index = null;
        foreach ($rows as $rowIndex => $row) {
            if ($row['Record ID'] === $id) {
                $index = $rowIndex;
                break;
            }
        }
        if ($index === null) {
            fail(404, 'Attendance record not found.');
        }
        array_splice($rows, $index, 1);
        $changed = true;
    }

    if ($changed) {
        writeCsv($file, $headers, $rows);
    }

    if ($method === 'GET') {
        $records = array_map(static function (array $row) use ($requiredHeaders): array {
            $record = ['Record ID' => $row['Record ID']];
            foreach ($requiredHeaders as $header) {
                $record[$header] = $row[$header] ?? '';
            }
            return $record;
        }, $rows);
        respond(200, ['records' => $records]);
    }

    if ($method === 'DELETE') {
        respond(200, ['success' => true]);
    }

    respond($method === 'POST' ? 201 : 200, ['record' => $savedRecord]);
} catch (Throwable $error) {
    error_log('Attendance API error: ' . $error->getMessage());
    fail(500, 'An unexpected error occurred while updating attendance.');
} finally {
    flock($file, LOCK_UN);
    fclose($file);
}
