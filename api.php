<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// TWO SEPARATE DATABASES
 $konek_azza  = mysqli_connect("localhost", "root", "", "azzahra2_azza");
 $konek_absen = mysqli_connect("localhost", "root", "", "azzahra2_absensi");

if (!$konek_azza) {
    echo json_encode(["success" => false, "message" => "Koneksi DB Azza gagal: " . mysqli_connect_error()]);
    exit;
}
if (!$konek_absen) {
    echo json_encode(["success" => false, "message" => "Koneksi DB Absensi gagal: " . mysqli_connect_error()]);
    exit;
}

 $action = isset($_GET['action']) ? $_GET['action'] : '';

switch ($action) {
    case 'get_orders':
        getOrders($konek_azza);
        break;
    case 'scan_rfid':
        scanRFID($konek_absen);
        break;
    default:
        echo json_encode(["success" => false, "message" => "Action tidak valid"]);
        break;
}

mysqli_close($konek_azza);
mysqli_close($konek_absen);


/* =========================================================
   GET ORDER LIST — uses azzahra2_azza
   ========================================================= */
function getOrders($konek) {
    $sql = "SELECT 
                c.cos_nama                                              AS nama_customer,
                o.ket_keluhan                                           AS keluhan,
                t.trans_status                                          AS status_order,
                DATEDIFF(CURDATE(), t.trans_tanggal)                    AS hari_menunggu
            FROM transaksi t
            JOIN costomer c       ON t.cos_kode = c.id_costomer
            JOIN order_list o     ON o.cos_kode = c.id_costomer
            WHERE t.trans_status IN ('Baru', 'Diproses')
                AND t.trans_tanggal != '0000-00-00'
            ORDER BY 
                t.trans_status ASC,
                hari_menunggu DESC";

    $result = mysqli_query($konek, $sql);

    if (!$result) {
        echo json_encode(["success" => false, "message" => "Query error: " . mysqli_error($konek)]);
        return;
    }

    $data = [];
    while ($row = mysqli_fetch_assoc($result)) {
        $data[] = $row;
    }

    echo json_encode(["success" => true, "data" => $data]);
}


/* =========================================================
   SCAN RFID — uses azzahra2_absensi
   ========================================================= */
function scanRFID($konek) {
    $input  = json_decode(file_get_contents('php://input'), true);
    $nokartu = isset($input['nokartu']) ? mysqli_real_escape_string($konek, trim($input['nokartu'])) : '';

    if ($nokartu === '') {
        echo json_encode(["success" => false, "message" => "No kartu kosong"]);
        return;
    }

    // Cek apakah karyawan terdaftar (DI DB ABSENSI)
    $emp = mysqli_query($konek, "SELECT nama FROM karyawan WHERE nokartu = '$nokartu'");
    if (mysqli_num_rows($emp) === 0) {
        echo json_encode(["success" => false, "message" => "Kartu tidak terdaftar"]);
        return;
    }
    $nama = mysqli_fetch_assoc($emp)['nama'];

    // WIB timezone
    date_default_timezone_set('Asia/Jakarta');
    $jam     = date('H:i:s');
    $tanggal = date('Y-m-d');
    $hour    = (int) date('H');

    // ---------- tentukan case berdasarkan jam ----------
    $case = 0;

    if ($hour >= 7 && $hour <= 9) {
        $case = 1;
    } elseif ($hour >= 11 && $hour <= 14) {
        $cek = mysqli_query($konek, "
            SELECT jam_istirahat
            FROM absensi
            WHERE nokartu = '$nokartu' AND tanggal = '$tanggal'
        ");

        if (mysqli_num_rows($cek) > 0) {
            $row = mysqli_fetch_assoc($cek);
            if ($row['jam_istirahat'] !== '00:00:00' && $row['jam_istirahat'] !== NULL) {
                $case = 3; 
            } else {
                $case = 2; 
            }
        } else {
            $case = 2; 
        }
    } elseif ($hour >= 16) {
        $case = 4;
    }

    if ($case === 0) {
        echo json_encode(["success" => false, "message" => "Di luar jam absensi"]);
        return;
    }

    $ok = updateAbsensi($konek, $nokartu, $tanggal, $jam, $case);

    if ($ok) {
        $messages = [
            1 => "Selamat datang, $nama!",
            2 => "$nama, istirahat dimulai.",
            3 => "$nama, istirahat selesai.",
            4 => "Selamat pulang, $nama!",
        ];

        echo json_encode([
            "success" => true,
            "message" => $messages[$case],
            "case"    => $case,
            "nama"    => $nama,
            "jam"     => $jam,
        ]);
    } else {
        echo json_encode(["success" => false, "message" => "Sudah diabsen untuk case ini"]);
    }
}


/* =========================================================
   UPDATE ABSENSI — uses azzahra2_absensi
   ========================================================= */
function updateAbsensi($konek, $no, $tanggal, $jam, $case) {

    $fields = [
        1 => 'jam_masuk',
        2 => 'jam_istirahat',
        3 => 'jam_kembali',
        4 => 'jam_pulang',
    ];

    if (!isset($fields[$case])) {
        return false;
    }

    $field = $fields[$case];

    $cek = mysqli_query($konek, "
        SELECT * FROM absensi
        WHERE nokartu = '$no' AND tanggal = '$tanggal'
    ");

    if (mysqli_num_rows($cek) === 0) {
        mysqli_query($konek, "
            INSERT INTO absensi (nokartu, tanggal, jam_masuk, jam_istirahat, jam_kembali, jam_pulang)
            VALUES ('$no', '$tanggal', '00:00:00', '00:00:00', '00:00:00', '00:00:00')
        ");
    }

    $query = mysqli_query($konek, "
        SELECT $field
        FROM absensi
        WHERE nokartu = '$no' AND tanggal = '$tanggal'
    ");

    $data = mysqli_fetch_assoc($query);

    if ($data && ($data[$field] === '00:00:00' || $data[$field] === NULL)) {
        mysqli_query($konek, "
            UPDATE absensi
            SET $field = '$jam'
            WHERE nokartu = '$no' AND tanggal = '$tanggal'
        ");
        return true;
    }

    return false;
}