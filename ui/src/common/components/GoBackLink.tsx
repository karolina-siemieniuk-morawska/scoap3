import React, { MouseEventHandler } from 'react';

import LinkLikeButton from './LinkLikeButton/LinkLikeButton';

const GoBackLink = ({
  children,
  onClick,
}: {
  children: string;
  onClick: MouseEventHandler<HTMLElement>;
}) => {
  return (
    <LinkLikeButton color="blue big" onClick={onClick}>
      {children}
    </LinkLikeButton>
  );
};

GoBackLink.defaultProps = {
  children: 'go back',
};

export default GoBackLink;
