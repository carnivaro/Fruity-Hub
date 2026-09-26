/* ==========================================
   TOAST NOTIFICATION
========================================== */

function showToast(message,type="success"){

    const toast=document.getElementById("toast");

    const text=document.getElementById("toastMessage");

    if(!toast || !text) return;

    toast.className="toast";

    toast.classList.add(type);

    text.textContent=message;

    toast.classList.add("show");

    setTimeout(()=>{

        toast.classList.remove("show");

    },3000);

}