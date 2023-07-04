function displayAlert()
{
    if (document.getElementById("loginalertbox") == null)
        return;
    document.getElementById("loginalertbox").style.display = "block";

    document.getElementById("closeLoginAlert").addEventListener("click", function() {
        document.getElementById("loginalertbox").style.display = "none";
    });
    setTimeout(removeAlert, 5000);
}

function removeAlert()
{
    document.getElementById("loginalertbox").style.display = "none";
}

displayAlert();