import hands

import asyncio
from time import sleep

import cv2
import numpy as np
from viam.components.motor import Motor
from viam.components.camera import Camera
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.media.video import CameraMimeType


async def connect():
    creds = Credentials(
        type='robot-location-secret',
        payload='3rn6lwpqwh5xzra3sy33x8ul94b5s20zf66ghe6v9bny577z')
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address('robot6-main.wkhwbmlw2g.viam.cloud', opts)

im = None

async def request_speeds(lmotor: Motor, rmotor: Motor, lspeed: float, rspeed: float):
    await asyncio.gather(
        lmotor.set_power(power=min(1, max(-1, lspeed))),
        rmotor.set_power(power=min(1, max(-1, rspeed))),
    )

robot = None

async def main():
    global robot
    robot = await connect()
    detector = hands.HandDetector()

    print(robot.resource_names)

    left = Motor.from_robot(robot=robot, name='left')
    right = Motor.from_robot(robot=robot, name='right')
    cam = Camera.from_robot(robot=robot, name='cam')

    try:
        while True:
            print('requesting first')
            pil_im = await cam.get_image(mime_type=CameraMimeType.VIAM_RGBA)
            print('recieved first')
            cv2_im = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGBA2BGR)

            cv2_im_labelled = detector.findHands(cv2_im)
            cv2.imwrite('feed.png', cv2_im_labelled)
            hand1det = detector.findPosition(cv2_im_labelled, handNo=0)
            hand2det = detector.findPosition(cv2_im_labelled, handNo=1)
            detections = {"left": None, "right": None}

            if not hand1det:
                pass
            elif hand1det[20][1] < hand1det[4][1]: # if pinky x < thumb x
                detections['left'] = hand1det
            else:
                detections['right'] = hand1det

            if not hand2det:
                pass
            elif hand2det[20][1] < hand2det[4][1]:
                detections['left'] = hand2det
            else:
                detections['right'] = hand2det

            ltop = detections['left'] is not None and detections['left'][4][2] < 0.5
            rtop = detections['right'] is not None and detections['right'][4][2] < 0.5
            print('requesting second')
            pil_im2 = await cam.get_image(mime_type=CameraMimeType.VIAM_RGBA)
            print('recieved second')

            if ltop and rtop and detections['left'][20][2] > detections['right'][20][2]:
                # if left pinky is farther right than right pinky
                # slow/stop
                await request_speeds(left, right, 0, 0)
            elif ltop and rtop:
                # forward
                power = 2 * (detections['right'][4][2] - detections['left'][4][2])
                await request_speeds(left, right, power, power)
            elif ltop and detections['right'] is not None:
                # turn left
                await request_speeds(left, right, 0.2, 0.5)
            elif rtop and detections['left'] is not None:
                # turn right
                await request_speeds(left, right, 0.5, 0.2)
            elif detections['left'] is not None and detections['right'] is not None:
                # go back
                await request_speeds(left, right, -0.5, -0.5)
            else:
                print(f'hands: {ltop=}, {rtop=}, {detections=}')
    except KeyboardInterrupt:
        print('interrupted')
        pass
    finally:
        print('closing')
        await robot.close()

if __name__ == '__main__':
    asyncio.run(main())
