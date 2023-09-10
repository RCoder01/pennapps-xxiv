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
from viam.components.base.base import Base


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
        self.base = Base.from_robot(robot=self.robot, name='viam_base')
        self.cam = Camera.from_robot(robot=self.robot, name='cam')
        self.detector = hands.HandDetector()

    # async def request_speeds(self, lspeed: float, rspeed: float):
    #     print(f'requesting: {lspeed=}, {rspeed=}')
        # await self.lmotor.set_power(power=min(1, max(-1, lspeed)))
        # await self.rmotor.set_power(power=min(1, max(-1, rspeed)))
        # if lspeed == rspeed == 0:

        # elif lspeed == rspeed:
        #     await self.base.move_straight(200,400)
        # elif lspeed < rspeed:
        #     await self.base.spin(30, 60)
        # elif rspeed < lspeed:
        #     await self.base.spin(-30, 60);

    async def handle_detections(self, pil_im: Image):
        # cv2_im = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGBA2BGR)
        cv2_im = pil_im

        cv2_im_labelled = self.detector.findHands(cv2_im)
        cv2.imwrite('feed.png', cv2_im_labelled)
        hand1det = self.detector.findPosition(cv2_im_labelled, handNo=0)
        hand2det = self.detector.findPosition(cv2_im_labelled, handNo=1)
        detections = {"left": None, "right": None}

        cv2.imshow("Image", cv2_im_labelled)
        cv2.waitKey(1)

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
        if detections['left'] is not None and detections['right'] is not None:
            hdiff = detections['left'][4][2] - detections['right'][4][2]
        else:
            hdiff = 0

        if hdiff > 0.25:
            # turn left
            await self.base.spin(60, 300)
        elif hdiff < -0.25 :
            # turn right
            await asyncio.gather(
                self.lmotor.go_for(40, 1),
                self.rmotor.go_for(40, -1)
            )
            # await self.base.move_straight(60, -120)
        if ltop and rtop and detections['left'][20][1] > detections['right'][20][1]:
            # if left pinky is farther right than right pinky
            # slow/stop
            await self.base.move_straight(0, 0)
        elif ltop and rtop:
            # forward
            power = 2 * (detections['right'][4][2] - detections['left'][4][2])
            await self.base.move_straight(200, 400)
        elif detections['left'] is not None and detections['right'] is not None:
            # go back
            await self.base.move_straight(-200, 400)
        else:
            # await self.request_speeds(0, 0)
            await self.base.move_straight(0,0)
            print(f'hands: {ltop=}, {rtop=}')

    async def main(self):
        await self.connect()

        print(self.robot.resource_names)

        self.cam = cv2.VideoCapture(0)
        try:
            while True:
                print('requesting')
                _, pil_im = self.cam.read()
                # pil_im = await self.cam.get_image(mime_type=CameraMimeType.VIAM_RGBA)
                print('recieved')
                await self.handle_detections(pil_im)
                # await asyncio.sleep(0.2)
        except KeyboardInterrupt:
            print('interrupted')
            pass
        except BaseException as e:
            print(e)
            raise
        finally:
            print('closing')
            await self.robot.close()

if __name__ == '__main__':
    asyncio.run(Robot().main())

    # async def main():
    #     creds = Credentials(
    #         type='robot-location-secret',
    #         payload='3rn6lwpqwh5xzra3sy33x8ul94b5s20zf66ghe6v9bny577z')
    #     opts = RobotClient.Options(
    #         refresh_interval=0,
    #         dial_options=DialOptions(credentials=creds)
    #     )
    #     robot =  await RobotClient.at_address('robot6-main.wkhwbmlw2g.viam.cloud', opts)
    #     motor = Base.from_robot(robot=robot, name='viam_base')
    #     await motor.move_straight(100, 200)
    #     await robot.close()

    # asyncio.run(main())
