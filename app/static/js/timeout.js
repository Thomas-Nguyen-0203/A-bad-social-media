let logoutBomb = null;
let extend = false;
const timeLimit = 1000*60*5;
const logoutUrl = window.location.origin + "/logout"
const resetUrl = window.location.origin + "/reset_timer"

function setTimeOutBomb()
{
    logoutBomb = setTimeout(
        () => {
            window.open(logoutUrl, "_self");
        },
        timeLimit
    );

    promtTimeout = setTimeout(
        () => {
            document.getElementById("alertbox").style.display = "block";

            document.getElementById("stay_logged_in").addEventListener("click", function() {
                document.getElementById("alertbox").style.display = "none";
                    clearTimeout(logoutBomb);
                    setTimeOutBomb();

                    fetch(
                        resetUrl,
                        {
                            method: "GET"
                        }
                    )
            });
        },
        timeLimit + 10000
    );

    document.getElementById("logout").addEventListener("click", function() {
        window.open(logoutUrl, "_self");
    });

    document.getElementById("closealert").addEventListener("click", function() {
        window.open(logoutUrl, "_self");
    });
}

setTimeOutBomb();