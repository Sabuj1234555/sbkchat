let url = "http://127.0.0.1:8000/"

async function fetch_user() {
    try {
        const response = await fetch(`${url}user/auth/`, {
            method: "post",
            headers:{
                "Content-Type":"application/json"

            },
            body: JSON.stringify({
                username: "juyel",
                password: "sobuj369"
            })
        })
        console.log(response.status)
        const data = await response.json()

        console.log(data)
    }catch(err){
        console.log(err)
    }
}
fetch_user()