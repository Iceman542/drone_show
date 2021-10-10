using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Threading;

public class Drone : MonoBehaviour
{
    private Rigidbody m_drone_rigidbody;
    private Vector3 m_flow_manager_start_pos;
    private Vector3 m_flow_manager_pos;
    private float m_flow_manager_speed;

    // Start is called before the first frame update
    void Start()
    {
        Debug.Log(String.Format("Drone Initializing - {0}", gameObject.name));

        m_drone_rigidbody = gameObject.GetComponent<Rigidbody>();
        m_flow_manager_pos = Vector3.zero;
        m_flow_manager_speed = 0f;
    }

    // Update is called once per frame
    void Update()
    {
        /* ALTIMETER */
        /*
        if (Input.GetKeyDown(KeyCode.W))
            m_pos.y += 1;
        if (Input.GetKeyDown(KeyCode.X))
        {
            if (m_pos.y > 0)
                m_pos.y -= 1;
        }
        if (Input.GetKeyDown(KeyCode.RightArrow))
            m_pos.x += 1;

        if (Input.GetKeyDown(KeyCode.LeftArrow))
            m_pos.x -= 1;

        if (Input.GetKeyDown(KeyCode.UpArrow))
            m_pos.z += 1;

        if (Input.GetKeyDown(KeyCode.DownArrow))
            m_pos.z -= 1;
        */
    }

    public void FlowManagerStartPosition(Vector3 pos, float speed)
    {
        m_flow_manager_start_pos.x = pos.x;
        m_flow_manager_start_pos.y = pos.y;
        m_flow_manager_start_pos.z = pos.z;

        // ISSUE1: y=z / z=y
        // ISSUE2: -40 is upstage y=-y
        // ISSUE3: 20:1 location factor

        m_flow_manager_pos.x = pos.x;
        m_flow_manager_pos.y = pos.z;
        m_flow_manager_pos.z = pos.y;
        m_flow_manager_speed = speed;
    }

    public void FlowManagerPosition(Vector3 pos, float speed)
    {
        pos.x += m_flow_manager_start_pos.x;
        pos.y += m_flow_manager_start_pos.y;
        pos.z += m_flow_manager_start_pos.z;

        // ISSUE1: y=z / z=y
        // ISSUE2: -40 is upstage y=-y
        // ISSUE3: 20:1 location factor

        m_flow_manager_pos.x = pos.x;
        m_flow_manager_pos.y = pos.z;
        m_flow_manager_pos.z = pos.y;
        m_flow_manager_speed = speed;

        //Debug.Log(String.Format("FlowManagerPosition:: {0}, {1}, {2}, {3}", m_flow_manager_pos.x, m_flow_manager_pos.y, m_flow_manager_pos.z, speed));
    }

    private void FixedUpdate()
    {
        Vector3 source_pos = m_drone_rigidbody.transform.position;
        Vector3 dest_pos = m_flow_manager_pos;
        float speed = m_flow_manager_speed; 

        //Debug.Log("source_pos " + source_pos.x + " " + source_pos.y + " " + source_pos.z);
        //Debug.Log("dest_pos " + dest_pos.x + " " + dest_pos.y + " " + dest_pos.z);

        m_drone_rigidbody.transform.position = Vector3.MoveTowards(source_pos, dest_pos, speed);
        //drone_rigidbody.position = pos;
        //drone_rigidbody.MovePosition(m_pos);
    }

    private void OnCollisionEnter(Collision collision)
    {
        Debug.Log(collision.gameObject.name);

        /*
        drone_rigidbody.isKinematic = true;
        if (collision.gameObject.name == "Floor")
        {
            //drone_rigidbody.velocity = Vector3.zero;
        }
        */
    }

    private void OnCollisionExit(Collision collision)
    {

    }
}
