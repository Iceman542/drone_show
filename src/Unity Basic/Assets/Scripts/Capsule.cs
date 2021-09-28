using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Capsule : MonoBehaviour
{
    private float offset = (float)5.0;
    private bool bKeyPressed = false;
    [SerializeField] private Transform groundTransform = null;

    // Start is called before the first frame update
    void Start()
    {
        transform.position = new Vector3(0, 4, 6);
    }

    // Update is called once per frame
    void Update()
    {
        /*
        transform.position = new Vector3(1, this.offset, 7);
        this.offset += (float)0.01;
        */
        if (Input.GetKeyDown(KeyCode.Space))
        {
            bKeyPressed = true;
            Debug.Log("update");
        }
    }
    private void FixedUpdate()
    {
        if (Physics.OverlapSphere(groundTransform.position, 0.1f).Length == 1)
        {
            return;
        }

        if (bKeyPressed)
        {
            GetComponent<Rigidbody>().AddForce(Vector3.up * 3, ForceMode.VelocityChange);
            bKeyPressed = false;
        }
    }

    private void OnCollisionEnter(Collision collision)
    {
        
    }

    private void OnCollisionExit(Collision collision)
    {
        
    }
}
