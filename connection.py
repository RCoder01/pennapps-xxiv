import hands

import asyncio
from time import sleep

import cv2
import numpy as np
from PIL.Image import Image
from viam.components.motor import Motor
from viam.components.camera import Camera
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.media.video import CameraMimeType


class Robot:
    async def connect(self):
        creds = Credentials(
            type='robot-location-secret',
            payload='3rn6lwpqwh5xzra3sy33x8ul94b5s20zf66ghe6v9bny577z')
        opts = RobotClient.Options(
            refresh_interval=0,
            dial_options=DialOptions(credentials=creds)
        )
        self.robot =  await RobotClient.at_address('robot6-main.wkhwbmlw2g.viam.cloud', opts)
        self.lmotor = Motor.from_robot(robot=self.robot, name='left')
        self.rmotor = Motor.from_robot(robot=self.robot, name='right')
        self.cam = Camera.from_robot(robot=self.robot, name='cam')
        self.detector = hands.HandDetector()

    async def request_speeds(self, lspeed: float, rspeed: float):
        print(f'requesting: {lspeed=}, {rspeed=}')
        # await asyncio.gather(
        #     self.lmotor.set_power(power=min(1, max(-1, lspeed))),
        #     self.rmotor.set_power(power=min(1, max(-1, rspeed))),
        # )

    async def handle_detections(self, pil_im: Image):
        cv2_im = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGBA2BGR)

        cv2_im_labelled = self.detector.findHands(cv2_im)
        cv2.imwrite('feed.png', cv2_im_labelled)
        hand1det = self.detector.findPosition(cv2_im_labelled, handNo=0)
        hand2det = self.detector.findPosition(cv2_im_labelled, handNo=1)
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
        # print('requesting second')
        # pil_im2 = await cam.get_image(mime_type=CameraMimeType.VIAM_RGBA)
        # print('recieved second')

        if ltop and rtop and detections['left'][20][2] > detections['right'][20][2]:
            # if left pinky is farther right than right pinky
            # slow/stop
            await self.request_speeds(0, 0)
        elif ltop and rtop:
            # forward
            power = 2 * (detections['right'][4][2] - detections['left'][4][2])
            await self.request_speeds(power, power)
        elif ltop and detections['right'] is not None:
            # turn left
            await self.request_speeds(0.2, 0.5)
        elif rtop and detections['left'] is not None:
            # turn right
            await self.request_speeds(0.5, 0.2)
        elif detections['left'] is not None and detections['right'] is not None:
            # go back
            await self.request_speeds(-0.5, -0.5)
        else:
            print(f'hands: {ltop=}, {rtop=}, {detections=}')

    async def main(self):
        await self.connect()

        print(self.robot.resource_names)

        try:
            while True:
                print('requesting')
                pil_im = await self.cam.get_image(mime_type=CameraMimeType.VIAM_RGBA)
                print('recieved')
                await self.handle_detections(pil_im)
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print('interrupted')
            pass
        finally:
            print('closing')
            await self.robot.close()

if __name__ == '__main__':
    asyncio.run(Robot().main())
