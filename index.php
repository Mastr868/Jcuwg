<?php
// ========================================
// بخش PHP: مدیریت کاربران و پست‌ها
// ========================================
session_start();

// فایل‌های JSON (اگر وجود ندارند، ایجاد می‌شوند)
if (!file_exists('users.json')) file_put_contents('users.json', '{"users": []}');
if (!file_exists('posts.json')) file_put_contents('posts.json', '{"posts": []}');

// توابع کاربردی
function redirect($url) {
    header("Location: $url");
    exit;
}

// پردازش فرم ثبت‌نام
if (isset($_POST['register'])) {
    $users = json_decode(file_get_contents('users.json'), true);
    $newUser = [
        'id' => count($users['users']) + 1,
        'username' => $_POST['username'],
        'password' => password_hash($_POST['password'], PASSWORD_BCRYPT)
    ];
    $users['users'][] = $newUser;
    file_put_contents('users.json', json_encode($users));
    $_SESSION['user'] = $newUser['username'];
    redirect('index.php');
}

// پردازش فرم ورود
if (isset($_POST['login'])) {
    $users = json_decode(file_get_contents('users.json'), true);
    foreach ($users['users'] as $user) {
        if ($user['username'] === $_POST['username'] && password_verify($_POST['password'], $user['password'])) {
            $_SESSION['user'] = $user['username'];
            redirect('index.php');
        }
    }
    $error = "نام کاربری یا رمز عبور اشتباه است!";
}

// پردازش آپلود پست
if (isset($_POST['upload']) && isset($_SESSION['user'])) {
    $targetDir = "uploads/";
    if (!is_dir($targetDir)) mkdir($targetDir);
    $fileName = uniqid() . basename($_FILES['media']['name']);
    $targetFile = $targetDir . $fileName;
    
    if (move_uploaded_file($_FILES['media']['tmp_name'], $targetFile)) {
        $posts = json_decode(file_get_contents('posts.json'), true);
        $newPost = [
            'id' => count($posts['posts']) + 1,
            'user' => $_SESSION['user'],
            'media' => $targetFile,
            'timestamp' => date('Y-m-d H:i:s')
        ];
        $posts['posts'][] = $newPost;
        file_put_contents('posts.json', json_encode($posts));
    }
}

// خروج کاربر
if (isset($_GET['logout'])) {
    session_destroy();
    redirect('index.php');
}

// خواندن پست‌ها
$posts = json_decode(file_get_contents('posts.json'), true);
?>
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>سایت اشتراک‌گذاری</title>
    <style>
        /* CSS در همین فایل */
        body { font-family: Tahoma; background: #f5f5f5; }
        .post { background: white; padding: 15px; margin: 10px; border-radius: 5px; }
        img, video { max-width: 300px; display: block; }
    </style>
</head>
<body>
    <!-- منوی بالا -->
    <div style="background: #333; color: white; padding: 10px;">
        <?php if (isset($_SESSION['user'])): ?>
            <span>سلام <?= $_SESSION['user'] ?>!</span>
            <a href="?logout" style="color: white;">خروج</a>
        <?php else: ?>
            <a href="#login" style="color: white;">ورود</a>
        <?php endif; ?>
    </div>

    <!-- فرم لاگین/ثبت‌نام -->
    <?php if (!isset($_SESSION['user'])): ?>
        <div id="login" style="margin: 20px;">
            <h2>ورود/ثبت‌نام</h2>
            <?php if (isset($error)) echo "<p style='color: red;'>$error</p>"; ?>
            <form method="post">
                <input type="text" name="username" placeholder="نام کاربری" required>
                <input type="password" name="password" placeholder="رمز عبور" required>
                <button type="submit" name="login">ورود</button>
                <button type="submit" name="register">ثبت‌نام</button>
            </form>
        </div>
    <?php else: ?>
        <!-- فرم آپلود -->
        <div style="margin: 20px;">
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="media" accept="image/*, video/*" required>
                <button type="submit" name="upload">آپلود</button>
            </form>
        </div>
    <?php endif; ?>

    <!-- نمایش پست‌ها -->
    <div style="margin: 20px;">
        <h2>پست‌ها</h2>
        <?php foreach ($posts['posts'] as $post): ?>
            <div class="post">
                <p>کاربر: <?= $post['user'] ?> (<?= $post['timestamp'] ?>)</p>
                <?php if (strpos($post['media'], 'image') !== false): ?>
                    <img src="<?= $post['media'] ?>">
                <?php else: ?>
                    <video src="<?= $post['media'] ?>" controls></video>
                <?php endif; ?>
            </div>
        <?php endforeach; ?>
    </div>

    <!-- جاوااسکریپت -->
    <script>
        // پیام‌های تعاملی
        if (window.location.hash === '#login') {
            document.getElementById('login').scrollIntoView();
        }
    </script>
</body>
</html>
