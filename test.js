let url = "https://sbkchat.onrender.com/"

async function fetch_user() {
    try {
        const response = await fetch(`${url}user/auth/`, {
            method: "post",
            headers:{
                "Content-Type":"application/json"

            },
            body: JSON.stringify({
                username: "sobuj",
                password: "sobuj@369"
            })
        })
        console.log(response.status)
        const data = await response.json()

        console.log(data)
    }catch(err){
        console.log(err)
    }
}
// fetch_user()

async function check(){
    try{
        const response = await fetch(`${url}user/check-auth`,{
            method:"get",
            headers:{
                "Content-Type":"application/json",
                'Authorization':"Token 33c799cf3991cd1aec76139760f048cebb79f43e"
            }
        })
        const data = await response.json();
        console.log(data)
    }catch(err){
        console.log(err)
    }
}

check()