/* 校园咸鱼 - 前端交互脚本 */

// Flash 消息自动消失
document.addEventListener("DOMContentLoaded", function() {
    var flashes = document.querySelectorAll(".flash");
    flashes.forEach(function(el) {
        setTimeout(function() {
            el.style.transition = "opacity 0.5s";
            el.style.opacity = "0";
            setTimeout(function() {
                el.style.display = "none";
            }, 500);
        }, 3000);
    });

    // 图片懒加载
    var lazyImages = document.querySelectorAll("img[data-src]");
    if ("IntersectionObserver" in window) {
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute("data-src");
                    observer.unobserve(img);
                }
            });
        });
        lazyImages.forEach(function(img) {
            observer.observe(img);
        });
    }

    // 确认删除
    var deleteForms = document.querySelectorAll("form[onsubmit*='confirm']");
    deleteForms.forEach(function(form) {
        form.addEventListener("submit", function(e) {
            var msg = form.getAttribute("onsubmit").match(/confirm\('([^']+)'\)/);
            if (msg && !confirm(msg[1])) {
                e.preventDefault();
            }
        });
    });
});

// 格式化价格
function formatPrice(price) {
    return parseFloat(price).toFixed(2);
}

// 图片预览函数(可被外部调用)
function previewImages(input) {
    var preview = document.getElementById("image-preview");
    if (!preview) return;
    preview.innerHTML = "";
    if (input.files) {
        Array.prototype.forEach.call(input.files, function(file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = document.createElement("img");
                img.src = e.target.result;
                img.className = "preview-img";
                preview.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    }
}

function previewAvatar(input) {
    var preview = document.getElementById("avatar-preview");
    if (!preview) return;
    preview.innerHTML = "";
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var img = document.createElement("img");
            img.src = e.target.result;
            img.className = "preview-img";
            preview.appendChild(img);
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// 举报表单切换
function toggleReportForm() {
    var form = document.getElementById("report-form");
    if (form) {
        form.style.display = form.style.display === "none" ? "block" : "none";
    }
}

// 聊天自动滚动到底部
function scrollToBottom() {
    var messages = document.getElementById("chat-messages");
    if (messages) {
        messages.scrollTop = messages.scrollHeight;
    }
}

window.onload = scrollToBottom;
