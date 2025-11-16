import { useState, useCallback } from "react"

const useSessionAPI = () => {
    const [sessionId, setSessionId] = useState(null)

    const createSession = useCallback(async () => {
        try{
            const API_BASE_URL = "http://localhost:8000"
            const ENDPOINT = "/session"

            const resp = await fetch(API_BASE_URL + ENDPOINT, {
                method: 'POST',
            })

            if(!resp.ok) {
                console.error('Session creation failed with status ' + resp.status)
                return
            }

            setSessionId(resp.json()['session_id'])
            console.info('Session creation successful ' )
        } catch(error) {
            console.error("Session creation error", error)
            setSessionId(null)
        }
    }, [])

    return [
        sessionId,
        createSession
    ]
}

export default useSessionAPI